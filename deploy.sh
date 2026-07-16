#!/bin/bash

# TradeMind AI - Production Deployment Script
# This script automates the deployment process for production servers

set -e  # Exit on error

echo "=========================================="
echo "  TradeMind AI - Production Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Configuration variables (set these before running)
DEPLOY_USER="${DEPLOY_USER:-ubuntu}"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/var/www/trademind-ai}"
DOMAIN_NAME="${DOMAIN_NAME:-trademind.ai}"
EMAIL="${EMAIL:-admin@trademind.ai}"
DATABASE_NAME="${DATABASE_NAME:-trademind_db}"
DATABASE_USER="${DATABASE_NAME:-trademind_user}"
DATABASE_PASSWORD="${DATABASE_PASSWORD:-$(openssl rand -base64 32)}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 50)}"
REDIS_PASSWORD="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Check required environment variables
if [ -z "$DEPLOY_HOST" ]; then
    print_error "DEPLOY_HOST environment variable is required"
    echo "Usage: DEPLOY_HOST=your-server-ip sudo -E ./deploy.sh"
    exit 1
fi

print_info "Deploying to: $DEPLOY_HOST"
print_info "Domain: $DOMAIN_NAME"
print_info "Deploy path: $DEPLOY_PATH"

# Step 1: Update system packages
print_info "Updating system packages..."
apt-get update && apt-get upgrade -y
print_success "System updated"

# Step 2: Install required packages
print_info "Installing required packages..."
apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    supervisor \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    python3-dev \
    certbot \
    python3-certbot-nginx \
    nodejs \
    npm
print_success "Packages installed"

# Step 3: Create deploy user and directory
print_info "Setting up deployment directory..."
mkdir -p $DEPLOY_PATH
chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
print_success "Directory created: $DEPLOY_PATH"

# Step 4: Setup PostgreSQL
print_info "Configuring PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE $DATABASE_NAME;
CREATE USER $DATABASE_USER WITH PASSWORD '$DATABASE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USER;
\\c $DATABASE_NAME
GRANT ALL ON SCHEMA public TO $DATABASE_USER;
EOF
print_success "PostgreSQL configured"

# Step 5: Setup Redis
print_info "Configuring Redis..."
redis-cli CONFIG SET requirepass "$REDIS_PASSWORD"
systemctl restart redis
print_success "Redis configured"

# Step 6: Clone or update code
print_info "Deploying code..."
cd $DEPLOY_PATH
if [ -d ".git" ]; then
    git pull origin master
else
    git clone https://github.com/sudhir1041/AL-Trade.git .
fi
print_success "Code deployed"

# Step 7: Create virtual environment
print_info "Creating Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
print_success "Python environment ready"

# Step 8: Create .env file
print_info "Creating environment configuration..."
cat > .env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://$DATABASE_USER:$DATABASE_PASSWORD@localhost/$DATABASE_NAME
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME
CSRF_TRUSTED_ORIGINS=https://$DOMAIN_NAME,https://www.$DOMAIN_NAME
CELERY_BROKER_URL=redis://:$REDIS_PASSWORD@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:$REDIS_PASSWORD@localhost:6379/2
EOF
print_success "Environment configured"

# Step 9: Run migrations
print_info "Running database migrations..."
python manage.py migrate
print_success "Migrations completed"

# Step 10: Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

# Step 11: Create superuser if not exists
print_info "Creating admin user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin_password = "$(openssl rand -base64 16)"
    User.objects.create_superuser('admin', 'admin@$DOMAIN_NAME', admin_password)
    with open('/tmp/admin_credentials.txt', 'w') as f:
        f.write(f'Admin Username: admin\\nAdmin Password: {admin_password}\\n')
    print('Superuser created. Credentials saved to /tmp/admin_credentials.txt')
else:
    print('Superuser already exists')
EOF
print_success "Admin user ready"

# Step 12: Setup Gunicorn systemd service
print_info "Configuring Gunicorn..."
cat > /etc/systemd/system/trademind-gunicorn.service << EOF
[Unit]
Description=gunicorn daemon for TradeMind AI
After=network.target

[Service]
User=$DEPLOY_USER
Group=www-data
WorkingDirectory=$DEPLOY_PATH/backend
ExecStart=$DEPLOY_PATH/backend/venv/bin/gunicorn --access-logfile - \\
    --workers 4 \\
    --bind unix:/run/gunicorn.sock \\
    trademind_ai.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start trademind-gunicorn
systemctl enable trademind-gunicorn
print_success "Gunicorn configured"

# Step 13: Setup Celery worker
print_info "Configuring Celery worker..."
cat > /etc/systemd/system/trademind-celery.service << EOF
[Unit]
Description=Celery Worker Service for TradeMind AI
After=network.target

[Service]
User=$DEPLOY_USER
Group=www-data
WorkingDirectory=$DEPLOY_PATH/backend
EnvironmentFile=$DEPLOY_PATH/backend/.env
ExecStart=$DEPLOY_PATH/backend/venv/bin/celery -A trademind_ai worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start trademind-celery
systemctl enable trademind-celery
print_success "Celery worker configured"

# Step 14: Setup Celery beat
print_info "Configuring Celery beat..."
cat > /etc/systemd/system/trademind-celery-beat.service << EOF
[Unit]
Description=Celery Beat Service for TradeMind AI
After=network.target

[Service]
User=$DEPLOY_USER
Group=www-data
WorkingDirectory=$DEPLOY_PATH/backend
EnvironmentFile=$DEPLOY_PATH/backend/.env
ExecStart=$DEPLOY_PATH/backend/venv/bin/celery -A trademind_ai beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start trademind-celery-beat
systemctl enable trademind-celery-beat
print_success "Celery beat configured"

# Step 15: Setup Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/trademind-ai << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location = /.well-known/acme-challenge/ {
        allow all;
        default_type "text/plain";
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    location /static/ {
        alias $DEPLOY_PATH/backend/static/;
    }

    location /media/ {
        alias $DEPLOY_PATH/backend/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/trademind-ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
mkdir -p /var/www/certbot
nginx -t
systemctl restart nginx
print_success "Nginx configured"

# Step 16: Setup SSL with Let's Encrypt
print_info "Setting up SSL certificate..."
certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email $EMAIL
systemctl reload nginx
print_success "SSL certificate installed"

# Step 17: Configure firewall
print_info "Configuring firewall..."
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
print_success "Firewall configured"

# Step 18: Setup monitoring and logging
print_info "Setting up log rotation..."
cat > /etc/logrotate.d/trademind-ai << EOF
$DEPLOY_PATH/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $DEPLOY_USER www-data
    sharedscripts
    postrotate
        systemctl reload trademind-gunicorn > /dev/null 2>&1 || true
    endscript
}
EOF
print_success "Log rotation configured"

# Step 19: Health check
print_info "Running health checks..."
sleep 5
if systemctl is-active --quiet trademind-gunicorn; then
    print_success "Gunicorn is running"
else
    print_error "Gunicorn failed to start"
fi

if systemctl is-active --quiet trademind-celery; then
    print_success "Celery worker is running"
else
    print_error "Celery worker failed to start"
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx failed to start"
fi

# Final summary
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Application URL: https://$DOMAIN_NAME"
echo "API Endpoint: https://$DOMAIN_NAME/api/v1/"
echo "Admin Panel: https://$DOMAIN_NAME/admin/"
echo ""
echo "Services running:"
echo "  ✓ Gunicorn (Django app)"
echo "  ✓ Celery Worker (background tasks)"
echo "  ✓ Celery Beat (scheduled tasks)"
echo "  ✓ Nginx (reverse proxy)"
echo "  ✓ PostgreSQL (database)"
echo "  ✓ Redis (cache & broker)"
echo ""
echo "Admin credentials saved to: /tmp/admin_credentials.txt"
echo ""
echo "Useful commands:"
echo "  View logs: journalctl -u trademind-gunicorn -f"
echo "  Restart services: systemctl restart trademind-gunicorn trademind-celery nginx"
echo "  Check status: systemctl status trademind-gunicorn trademind-celery nginx"
echo ""
echo "Security reminders:"
echo "  - Change default admin password immediately"
echo "  - Keep system updated: apt update && apt upgrade"
echo "  - Monitor logs regularly"
echo "  - Backup database regularly"
echo ""

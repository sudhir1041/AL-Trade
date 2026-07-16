#!/bin/bash

# TradeMind AI - Local Development Setup Script
# This script sets up the complete development environment on your local machine

set -e  # Exit on error

echo "=========================================="
echo "  TradeMind AI - Local Setup"
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

# Check if running in correct directory
if [ ! -f "backend/manage.py" ] && [ ! -f "manage.py" ]; then
    print_error "Please run this script from the trademind-ai root directory"
    exit 1
fi

# Determine backend directory
if [ -d "backend" ]; then
    BACKEND_DIR="backend"
else
    BACKEND_DIR="."
fi

cd $BACKEND_DIR

# Step 1: Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3.10+ not found. Please install Python 3.10 or higher."
    exit 1
fi

# Step 2: Create virtual environment
print_info "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Step 3: Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Step 4: Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"

# Step 5: Install dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Step 6: Check for PostgreSQL
print_info "Checking database setup..."
if command -v psql &> /dev/null; then
    print_success "PostgreSQL found"
else
    print_info "PostgreSQL not found. Using SQLite for development."
fi

# Step 7: Run migrations
print_info "Running database migrations..."
python manage.py migrate
print_success "Migrations completed"

# Step 8: Create superuser (optional)
print_info "Creating admin superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@trademind.ai', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
EOF
print_success "Admin user ready (username: admin, password: admin123)"

# Step 9: Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

cd ..

# Step 10: Setup frontend if exists
if [ -d "frontend" ]; then
    print_info "Setting up frontend..."
    cd frontend
    
    if command -v npm &> /dev/null; then
        print_success "Node.js/npm found"
        
        if [ ! -d "node_modules" ]; then
            print_info "Installing frontend dependencies..."
            npm install
            print_success "Frontend dependencies installed"
        else
            print_success "Frontend dependencies already installed"
        fi
    else
        print_info "Node.js not found. Skipping frontend setup."
    fi
    
    cd ..
fi

# Step 11: Start development services
print_info "Starting development server..."
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Backend API: http://localhost:8000/api/v1/"
echo "API Docs: http://localhost:8000/api/docs/"
echo "Admin Panel: http://localhost:8000/admin/"
echo ""
echo "Frontend (if installed): http://localhost:3000/"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "To start the backend server manually:"
echo "  cd $BACKEND_DIR"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "To start Celery worker:"
echo "  celery -A trademind_ai worker -l info"
echo ""
echo "To start Celery beat:"
echo "  celery -A trademind_ai beat -l info"
echo ""
echo "To start frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""

# Optional: Start server automatically
read -p "Do you want to start the development server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd $BACKEND_DIR
    source venv/bin/activate
    python manage.py runserver
fi

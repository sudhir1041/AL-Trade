# =============================================================================
# TradeMind AI – Backend Dockerfile
# Multi-stage build for lean, secure production images
# =============================================================================

# ─────────────────────────────────────────
# Stage 1 – base: system deps + Python deps
# ─────────────────────────────────────────
FROM python:3.13-slim AS base

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    # TA-Lib dependencies for technical analysis
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library (required by ta-lib Python package)
RUN wget -q https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ─────────────────────────────────────────
# Stage 2 – production: non-root, hardened
# ─────────────────────────────────────────
FROM base AS production

# Security: create a non-root user and group
RUN groupadd --gid 1001 trademind \
    && useradd --uid 1001 --gid trademind --shell /bin/bash \
       --create-home trademind

WORKDIR /app

# Copy application code with correct ownership
COPY --chown=trademind:trademind . .

# Create required runtime directories
RUN mkdir -p /app/staticfiles /app/media /app/logs /tmp/prometheus_multiproc \
    && chown -R trademind:trademind /app/staticfiles /app/media /app/logs /tmp/prometheus_multiproc

# Switch to non-root user
USER trademind

# Expose Django / Gunicorn port
EXPOSE 8000

# Health check – hits the Django health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default command – override in docker-compose for other workers
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

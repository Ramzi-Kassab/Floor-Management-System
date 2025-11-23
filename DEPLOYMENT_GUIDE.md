# Floor Management System - Deployment Guide

## 📋 Table of Contents
- [System Requirements](#system-requirements)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Celery & Redis Setup](#celery--redis-setup)
- [Web Server Configuration](#web-server-configuration)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Performance Optimization](#performance-optimization)
- [Security Hardening](#security-hardening)
- [Troubleshooting](#troubleshooting)

## 💻 System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **OS**: Ubuntu 20.04 LTS or newer / CentOS 8+

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: 100 Mbps+

### Software Dependencies
- Python 3.10 or newer
- PostgreSQL 13+ (or MySQL 8+)
- Redis 6+ (for Celery)
- Nginx or Apache
- Git

## ✅ Pre-Deployment Checklist

### Code Preparation
- [ ] All tests passing (`python manage.py test`)
- [ ] Code review completed
- [ ] Dependencies updated in requirements.txt
- [ ] Environment variables documented
- [ ] Static files collected
- [ ] Migrations verified

### Security
- [ ] SECRET_KEY changed to production value
- [ ] DEBUG = False in production
- [ ] ALLOWED_HOSTS configured
- [ ] CSRF settings verified
- [ ] SSL certificates obtained
- [ ] Firewall rules configured

### Database
- [ ] Database created
- [ ] Database user created with proper permissions
- [ ] Database backed up (if migrating)
- [ ] Connection tested

### Infrastructure
- [ ] Domain name configured
- [ ] DNS records set
- [ ] Email service configured
- [ ] Backup solution in place
- [ ] Monitoring tools set up

## 🔧 Development Deployment

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Floor-Management-System.git
cd Floor-Management-System
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create .env File
```bash
cp .env.example .env
nano .env  # Edit with your local settings
```

Example .env:
```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=floor_management
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Setup Database
```bash
# Create database
createdb floor_management

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Access at http://localhost:8000

## 🚀 Production Deployment

### Option 1: Ubuntu/Debian Server

#### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install System Dependencies
```bash
sudo apt install -y python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    nginx git supervisor
```

#### 3. Create Application User
```bash
sudo useradd -m -s /bin/bash floorapp
sudo su - floorapp
```

#### 4. Clone Repository
```bash
cd /home/floorapp
git clone https://github.com/yourusername/Floor-Management-System.git app
cd app
```

#### 5. Setup Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # WSGI server
```

#### 6. Create Production .env
```bash
nano .env
```

```env
DEBUG=False
SECRET_KEY=generate-a-strong-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=floor_management_prod
DB_USER=floorapp
DB_PASSWORD=strong-database-password
DB_HOST=localhost
DB_PORT=5432

# Use actual SMTP server for production
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### 7. Setup PostgreSQL Database
```bash
sudo -u postgres psql

-- In PostgreSQL:
CREATE DATABASE floor_management_prod;
CREATE USER floorapp WITH PASSWORD 'strong-database-password';
ALTER ROLE floorapp SET client_encoding TO 'utf8';
ALTER ROLE floorapp SET default_transaction_isolation TO 'read committed';
ALTER ROLE floorapp SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE floor_management_prod TO floorapp;
\q
```

#### 8. Run Migrations
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### 9. Configure Gunicorn
Create `/home/floorapp/app/gunicorn_config.py`:
```python
bind = "127.0.0.1:8000"
workers = 4  # 2-4 x CPU cores
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
errorlog = "/home/floorapp/app/logs/gunicorn-error.log"
accesslog = "/home/floorapp/app/logs/gunicorn-access.log"
loglevel = "info"
```

Create log directory:
```bash
mkdir -p /home/floorapp/app/logs
```

#### 10. Create Systemd Service for Gunicorn
```bash
sudo nano /etc/systemd/system/floorapp.service
```

```ini
[Unit]
Description=Floor Management System
After=network.target

[Service]
Type=notify
User=floorapp
Group=www-data
WorkingDirectory=/home/floorapp/app
Environment="PATH=/home/floorapp/app/venv/bin"
ExecStart=/home/floorapp/app/venv/bin/gunicorn \
    --config /home/floorapp/app/gunicorn_config.py \
    floor_mgmt.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 11. Start Gunicorn
```bash
sudo systemctl daemon-reload
sudo systemctl start floorapp
sudo systemctl enable floorapp
sudo systemctl status floorapp
```

## 🐳 Docker Deployment

### Dockerfile
Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -s /bin/bash floorapp && chown -R floorapp:floorapp /app
USER floorapp

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "floor_mgmt.wsgi:application"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: floor_management
      POSTGRES_USER: floorapp
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - floor_network

  redis:
    image: redis:7-alpine
    networks:
      - floor_network

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 floor_mgmt.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - floor_network

  celery:
    build: .
    command: celery -A floor_mgmt worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - floor_network

  celery-beat:
    build: .
    command: celery -A floor_mgmt beat --loglevel=info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    networks:
      - floor_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    networks:
      - floor_network

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  floor_network:
    driver: bridge
```

### Deploy with Docker
```bash
# Build and start
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

## 🌐 Web Server Configuration

### Nginx Configuration
Create `/etc/nginx/sites-available/floorapp`:

```nginx
upstream floorapp {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    location /static/ {
        alias /home/floorapp/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/floorapp/app/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://floorapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/floorapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔐 SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

## 🔄 Celery & Redis Setup

### Configure Celery with Supervisor
Create `/etc/supervisor/conf.d/floorapp-celery.conf`:

```ini
[program:floorapp-celery]
command=/home/floorapp/app/venv/bin/celery -A floor_mgmt worker --loglevel=info
directory=/home/floorapp/app
user=floorapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/floorapp/app/logs/celery-worker.log
stopwaitsecs=600

[program:floorapp-celery-beat]
command=/home/floorapp/app/venv/bin/celery -A floor_mgmt beat --loglevel=info
directory=/home/floorapp/app
user=floorapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/floorapp/app/logs/celery-beat.log
```

Reload Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

## 📊 Monitoring & Logging

### Configure Logging
Add to settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/floorapp/app/logs/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### System Monitoring Tools
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor processes
htop

# Monitor disk I/O
sudo iotop

# Monitor network
sudo nethogs
```

## 💾 Backup & Recovery

### Database Backup Script
Create `/home/floorapp/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/floorapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="floor_management_prod"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/floorapp/app/media

# Remove backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make executable and schedule:
```bash
chmod +x /home/floorapp/backup.sh

# Add to crontab
crontab -e
# Add line:
0 2 * * * /home/floorapp/backup.sh
```

## ⚡ Performance Optimization

### Database Optimization
```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_auditlog_timestamp ON floor_core_auditlog(timestamp DESC);
CREATE INDEX idx_auditlog_user ON floor_core_auditlog(user_id);
CREATE INDEX idx_activitylog_timestamp ON floor_core_activitylog(timestamp DESC);
```

### Django Optimization
Add to settings.py:
```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session cache
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

## 🔒 Security Hardening

### Security Checklist
```python
# settings.py production security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### Firewall Setup
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput --clear

# Check nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 2. Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U floorapp -d floor_management_prod -h localhost
```

#### 3. Gunicorn Not Starting
```bash
# Check logs
sudo journalctl -u floorapp -f

# Test gunicorn manually
/home/floorapp/app/venv/bin/gunicorn --bind 127.0.0.1:8000 floor_mgmt.wsgi:application
```

#### 4. Celery Tasks Not Running
```bash
# Check Celery workers
sudo supervisorctl status floorapp-celery

# Check Redis
redis-cli ping

# Restart Celery
sudo supervisorctl restart floorapp-celery
```

## 📞 Support

For deployment issues or questions, contact the DevOps team.

---

**Last Updated**: November 2024

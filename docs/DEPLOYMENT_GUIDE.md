# Floor Management System - Deployment Guide

## Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **PostgreSQL**: 13 or higher
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: Minimum 10GB free space
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

### Required Software
```bash
# Install Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install system dependencies
sudo apt install build-essential libpq-dev python3-dev
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Floor-Management-System
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Setup

#### Create PostgreSQL Database
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE floor_mgmt_db;
CREATE USER floor_mgmt_user WITH PASSWORD 'your_secure_password';
ALTER ROLE floor_mgmt_user SET client_encoding TO 'utf8';
ALTER ROLE floor_mgmt_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE floor_mgmt_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE floor_mgmt_db TO floor_mgmt_user;
\q
```

#### Configure Database Connection
Create `.env` file in project root:
```env
# Database
DB_NAME=floor_mgmt_db
DB_USER=floor_mgmt_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here-generate-a-long-random-string
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**Generate Secret Key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### 8. Load Initial Data (Optional)
```bash
# Load reference data
python manage.py loaddata fixtures/initial_data.json
```

## Running the Application

### Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

Access at: http://localhost:8000

### Production with Gunicorn
```bash
pip install gunicorn

# Run Gunicorn
gunicorn floor_mgmt.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Production with uWSGI
```bash
pip install uwsgi

# Run uWSGI
uwsgi --http :8000 --module floor_mgmt.wsgi --master --processes 4 --threads 2
```

## Web Server Configuration

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/Floor-Management-System/staticfiles/;
    }

    location /media/ {
        alias /path/to/Floor-Management-System/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName yourdomain.com

    Alias /static /path/to/Floor-Management-System/staticfiles
    <Directory /path/to/Floor-Management-System/staticfiles>
        Require all granted
    </Directory>

    Alias /media /path/to/Floor-Management-System/media
    <Directory /path/to/Floor-Management-System/media>
        Require all granted
    </Directory>

    ProxyPass /static !
    ProxyPass /media !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

## SSL/TLS Configuration

### Using Let's Encrypt (Certbot)
```bash
sudo apt install certbot python3-certbot-nginx

# For Nginx
sudo certbot --nginx -d yourdomain.com

# For Apache
sudo certbot --apache -d yourdomain.com
```

## Systemd Service (Production)

Create `/etc/systemd/system/floor-mgmt.service`:
```ini
[Unit]
Description=Floor Management System
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/Floor-Management-System
Environment="PATH=/path/to/Floor-Management-System/venv/bin"
ExecStart=/path/to/Floor-Management-System/venv/bin/gunicorn \
          --workers 4 \
          --bind unix:/run/floor-mgmt.sock \
          floor_mgmt.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable floor-mgmt
sudo systemctl start floor-mgmt
sudo systemctl status floor-mgmt
```

## Database Backup

### Manual Backup
```bash
pg_dump -U floor_mgmt_user floor_mgmt_db > backup_$(date +%Y%m%d).sql
```

### Automated Backup (Cron)
```bash
crontab -e
```

Add:
```cron
0 2 * * * pg_dump -U floor_mgmt_user floor_mgmt_db > /backups/floor_mgmt_$(date +\%Y\%m\%d).sql
```

### Restore from Backup
```bash
psql -U floor_mgmt_user floor_mgmt_db < backup_20251123.sql
```

## Monitoring and Logging

### Application Logs
Located in `logs/` directory:
- `django.log` - Application logs
- `error.log` - Error logs
- `access.log` - Access logs

### Log Rotation
Create `/etc/logrotate.d/floor-mgmt`:
```
/path/to/Floor-Management-System/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes
CREATE INDEX CONCURRENTLY idx_employee_status ON hr_employee(status);
CREATE INDEX CONCURRENTLY idx_jobcard_status ON production_jobcard(status);

-- Analyze tables
ANALYZE;
```

### Django Cache Configuration
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Static File Compression
```bash
pip install django-compressor
pip install django-storages  # For S3/cloud storage
```

## Security Checklist

- [ ] Change DEBUG to False in production
- [ ] Set strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Enable HTTPS/SSL
- [ ] Set secure cookie flags
- [ ] Configure CSRF protection
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database password security
- [ ] File upload restrictions
- [ ] Regular backups

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U floor_mgmt_user -d floor_mgmt_db -h localhost
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --no-input

# Check STATIC_ROOT in settings
python manage.py diffsettings | grep STATIC
```

### Permission Errors
```bash
# Fix ownership
sudo chown -R www-data:www-data /path/to/Floor-Management-System

# Fix permissions
chmod -R 755 /path/to/Floor-Management-System
```

## Health Checks

### Database Health
```bash
python manage.py check database
```

### Application Health
```bash
curl http://localhost:8000/health/
```

### System Resources
```bash
# Check memory
free -h

# Check disk space
df -h

# Check processes
ps aux | grep gunicorn
```

## Scaling

### Horizontal Scaling
- Deploy multiple application servers
- Use load balancer (Nginx, HAProxy)
- Shared database server
- Redis for session storage

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Enable caching
- Use CDN for static files

## Support

For issues and support:
- Documentation: `/docs/`
- Issue Tracker: GitHub Issues
- Email: support@example.com

---

**Deployment Date**: 2025-11-23
**Version**: 1.0.0
**Status**: Production Ready

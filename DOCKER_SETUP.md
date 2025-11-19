# Docker Setup Guide

## Quick Start

### Development Environment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

### Production Environment

```bash
# Start with production services (including Nginx and Redis)
docker-compose --profile production up -d

# View all running containers
docker ps

# Scale web workers
docker-compose --profile production up -d --scale web=3
```

## Service URLs

- **Web Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **Health Check**: http://localhost:8000/api/health/
- **Database**: localhost:5433 (PostgreSQL)
- **Redis**: localhost:6379 (when using production profile)

## Common Tasks

### Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Migrations

```bash
docker-compose exec web python manage.py migrate
```

### Collect Static Files

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Load Test Data

```bash
docker-compose exec web python manage.py loaddata fixtures/test_data.json
```

### Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Database Shell

```bash
docker-compose exec db psql -U postgres -d floor_management
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 web
```

### Backup Database

```bash
# Create backup
docker-compose exec db pg_dump -U postgres floor_management > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Or use the backup directory mounted in container
docker-compose exec db pg_dump -U postgres floor_management > /backups/backup.sql
```

### Restore Database

```bash
# From local file
docker-compose exec -T db psql -U postgres -d floor_management < backups/backup.sql

# From container backup
docker-compose exec db psql -U postgres -d floor_management < /backups/backup.sql
```

### Rebuild Containers

```bash
# Rebuild after code changes
docker-compose build web

# Rebuild without cache
docker-compose build --no-cache web

# Rebuild and restart
docker-compose up -d --build
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=floor_management
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# External DB Port (host machine)
DB_PORT_EXTERNAL=5433
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Docker Network                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Web    │  │   Redis  │  │  Nginx   │      │
│  │  Django  │──│  Cache   │──│  Proxy   │      │
│  │   :8000  │  │  :6379   │  │  :80     │      │
│  └────┬─────┘  └──────────┘  └──────────┘      │
│       │                                          │
│  ┌────▼─────┐                                   │
│  │    DB    │                                   │
│  │PostgreSQL│                                   │
│  │  :5432   │                                   │
│  └──────────┘                                   │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Volumes

- `postgres_data`: PostgreSQL database files (persistent)
- `redis_data`: Redis cache data (persistent)
- `static_volume`: Django static files
- `media_volume`: User uploaded files
- `logs_volume`: Application logs

## Health Checks

All services include health checks:

- **Database**: `pg_isready` every 10s
- **Web**: HTTP check on `/api/health/` every 30s
- **Redis**: `redis-cli ping` every 10s

Check health status:

```bash
docker-compose ps
```

## Troubleshooting

### Database Connection Failed

```bash
# Check if database is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Web Application Won't Start

```bash
# Check logs
docker-compose logs web

# Rebuild image
docker-compose build --no-cache web

# Check health
docker-compose exec web python manage.py check
```

### Port Already in Use

```bash
# Change port in docker-compose.yml
# Or stop the conflicting service

# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Reset Everything

```bash
# Nuclear option: delete everything and start fresh
docker-compose down -v --rmi all
docker-compose up -d --build
```

## Performance Optimization

### Production Settings

1. **Use Gunicorn instead of runserver**:

```dockerfile
# In Dockerfile, change CMD to:
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "floor_management.wsgi:application"]
```

2. **Enable Redis caching**:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

3. **Use Nginx for static files**:

Create `nginx/nginx.conf`:

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name localhost;

    location /static/ {
        alias /app/static/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Change default database password
- [ ] Set DEBUG=False in production
- [ ] Use HTTPS (configure Nginx SSL)
- [ ] Set restrictive ALLOWED_HOSTS
- [ ] Enable CSRF protection
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Enable database backups
- [ ] Monitor logs for suspicious activity

## Monitoring

### Resource Usage

```bash
# View resource usage
docker stats

# Specific container
docker stats floor_management_web
```

### Application Logs

```bash
# Real-time logs
docker-compose exec web tail -f logs/floor_management.log

# Error logs only
docker-compose logs web | grep ERROR
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and deploy
        run: |
          docker-compose build
          docker-compose up -d
          docker-compose exec -T web python manage.py migrate
```

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Verify configuration: `docker-compose config`
- Test database connection: `docker-compose exec web python manage.py dbshell`

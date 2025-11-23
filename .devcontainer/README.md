# Devcontainer Configuration for Floor Management System

This directory contains the configuration for GitHub Codespaces and VS Code Dev Containers.

## What's Included

### Services
- **Python 3.11** - Django application environment
- **PostgreSQL 15** - Database server
- **Redis 7** - Cache and Celery message broker

### VS Code Extensions
- Python language support with Pylance
- Django template support
- HTML/CSS/JavaScript tools
- Git tools (GitHub Copilot, GitLens)
- Code formatting (Black, Prettier)

### Automatic Setup
When the Codespace starts, it automatically:
1. Installs all Python dependencies from requirements.txt
2. Waits for PostgreSQL and Redis to be ready
3. Creates .env file with development settings
4. Runs database migrations
5. Creates a superuser (admin / admin123)
6. Collects static files

## Quick Start

After the Codespace is created:

```bash
# Start Django development server
python manage.py runserver 0.0.0.0:8000

# Start Celery worker (in another terminal)
celery -A floor_mgmt worker -l info

# Start Celery beat scheduler (in another terminal)
celery -A floor_mgmt beat -l info
```

## Access Points

- **Django App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Default Credentials

- **Username**: admin
- **Password**: admin123

## Environment Variables

The setup creates a `.env` file with:
- DEBUG=True
- Database connection settings
- Redis connection settings
- Celery configuration

## Customization

Edit these files to customize:
- `devcontainer.json` - Container configuration
- `docker-compose.yml` - Service definitions
- `Dockerfile` - Python environment
- `postCreateCommand.sh` - Setup script

## Ports

The following ports are forwarded:
- **8000** - Django development server
- **5432** - PostgreSQL
- **6379** - Redis

## Notes

- The PostgreSQL data is persisted in a Docker volume
- Redis is configured in-memory (data not persisted)
- The workspace is mounted at `/workspaces/Floor-Management-System`
- All Python packages are installed in the container, not your local machine

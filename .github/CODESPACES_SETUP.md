# Setting up Floor Management System in GitHub Codespaces

## Automatic Setup

When you create a Codespace, the following happens automatically:

1. ✅ **Python 3.11** environment created
2. ✅ **Docker** installed and configured
3. ✅ **Dependencies** installed from requirements.txt
4. ✅ **PostgreSQL** started in container
5. ✅ **Django** migrations run
6. ✅ **Test data** loaded
7. ✅ **Development server** started on port 8000

## What's Configured

### Ports
- **8000** - Django Web Server (auto-forwarded)
- **5433** - PostgreSQL Database (silent forward)

### VS Code Extensions
- Python
- Pylance
- Django
- Docker

### Post-Start Command
Runs `scripts/codespace_setup.sh` which:
- Starts Docker Compose
- Runs migrations
- Loads test data
- Checks templates
- Shows helpful information

## Accessing the Application

### Method 1: Notification Popup
Click "Open in Browser" when it appears

### Method 2: Ports Tab
1. Click "PORTS" tab at bottom
2. Find port 8000
3. Click globe icon 🌐

### Method 3: URL
```
https://<your-codespace-name>-8000.app.github.dev
```

## First Time Setup

### Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Check Everything Works
```bash
# Health check
curl http://localhost:8000/api/health/

# View logs
docker-compose logs -f web

# Run tests
docker-compose exec web python manage.py test
```

## Useful Commands

### Django Commands
```bash
# Django shell
docker-compose exec web python manage.py shell

# Check system
docker-compose exec web python manage.py check

# Create migrations
docker-compose exec web python manage.py makemigrations

# Run migrations
docker-compose exec web python manage.py migrate
```

### Docker Commands
```bash
# View logs
docker-compose logs -f web

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Development Commands
```bash
# Check templates
docker-compose exec web python scripts/check_templates.py

# Fix templates
docker-compose exec web python scripts/fix_templates.py --apply

# Run tests
docker-compose exec web python manage.py test
```

## Troubleshooting

### Database Not Ready
```bash
# Wait a bit longer, then restart
docker-compose restart db
sleep 10
docker-compose restart web
```

### Port Not Forwarding
```bash
# Check port visibility in Ports tab
# Make sure port 8000 is set to "Private" or "Public"
```

### Changes Not Reflecting
```bash
# Restart web server
docker-compose restart web

# Or rebuild
docker-compose up -d --build
```

## Performance Tips

- Codespace stops after 30 minutes of inactivity
- Commit your changes before stopping
- Use `docker-compose down` before stopping to clean up
- Delete codespace when done reviewing to save hours

## See Also

- **CODESPACES_GUIDE.md** - Complete guide
- **QUICK_START_GUIDE.md** - General setup guide
- **DOCKER_SETUP.md** - Docker documentation

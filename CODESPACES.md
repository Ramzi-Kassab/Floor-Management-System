# GitHub Codespaces Setup Guide

This repository is configured for **GitHub Codespaces** with automatic environment setup.

## Quick Start

### 1. Create a Codespace

**From GitHub Web:**
1. Go to the repository on GitHub
2. Click the **Code** button (green button)
3. Select the **Codespaces** tab
4. Click **Create codespace on claude/floor-management-system-01CfqtWsKbRnuzL7PipJZ3k2**

**From Command Line:**
```bash
gh codespace create --repo Ramzi-Kassab/Floor-Management-System --branch claude/floor-management-system-01CfqtWsKbRnuzL7PipJZ3k2
```

### 2. Wait for Setup

The Codespace will automatically:
- ✅ Install Python 3.11 environment
- ✅ Set up PostgreSQL 15 database
- ✅ Set up Redis 7 cache
- ✅ Install all Python dependencies
- ✅ Run database migrations
- ✅ Create superuser (admin / admin123)
- ✅ Configure VS Code extensions

**Setup takes approximately 3-5 minutes.**

### 3. Start Development Server

Once setup completes, run:

```bash
python manage.py runserver 0.0.0.0:8000
```

The Codespace will automatically forward port 8000 and show you a notification with the URL.

### 4. Access the Application

Click the notification or go to the **Ports** tab to open:
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **Theme Settings**: http://localhost:8000/core/theme-settings/

### 5. Login

Use these default credentials:
- **Username**: `admin`
- **Password**: `admin123`

## Features Included

### ✨ Complete Development Environment
- Python 3.11 with all dependencies
- PostgreSQL 15 database (automatically configured)
- Redis 7 for caching and Celery
- Pre-configured environment variables

### 🛠️ VS Code Extensions
- Python language support (Pylance)
- Django template syntax highlighting
- Black code formatter
- HTML/CSS/JavaScript tools
- Git tools (GitLens, GitHub Copilot)

### 🎨 Frontend Features Ready to Test
- **Custom Color System**: Choose any background, text, and primary colors
- **Real-time Dashboard**: Chart.js visualizations with auto-refresh
- **AJAX Filtering**: Live search on activity logs, audit logs, system events
- **Theme System**: Light/dark mode with live preview
- **Keyboard Shortcuts**: Power user features (press `?` for help)
- **Notification System**: Real-time notifications with desktop alerts

## Running Background Services

### Celery Worker
In a new terminal:
```bash
celery -A floor_mgmt worker -l info
```

### Celery Beat Scheduler
In a new terminal:
```bash
celery -A floor_mgmt beat -l info
```

## Database Access

### Django Shell
```bash
python manage.py shell
```

### PostgreSQL CLI
```bash
psql -h localhost -U floor_user -d floor_management
# Password: floor_password
```

### Redis CLI
```bash
redis-cli
```

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
pytest --cov=floor_app --cov-report=html

# Run specific test
python manage.py test floor_app.core.tests
```

## Creating Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations
```

## Environment Variables

Configuration is in `.env` file (auto-created):
```bash
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DB_NAME=floor_management
DB_USER=floor_user
DB_PASSWORD=floor_password
REDIS_URL=redis://localhost:6379/0
```

## Testing New Features

### 1. Custom Color System
1. Login at http://localhost:8000/admin/
2. Go to http://localhost:8000/core/theme-settings/
3. Scroll to **Custom Colors** section
4. Pick any colors using color pickers
5. Click **Save Settings**
6. Navigate to any page - your colors are applied!

### 2. Dashboard Visualizations
1. Go to http://localhost:8000/system/dashboard/
2. See real-time Chart.js visualizations
3. Click **Refresh** button or wait for auto-refresh
4. Toggle **Auto-refresh** on/off

### 3. AJAX Filtering
1. Go to http://localhost:8000/system/activity-logs/
2. Change filters in the form
3. See results update without page reload
4. Type in search field - results appear instantly

### 4. Keyboard Shortcuts
1. Press `?` anywhere - see all shortcuts
2. Press `g` then `d` - go to dashboard
3. Press `/` - focus search
4. Press `t` - toggle theme

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
pkill -f runserver
# Or use a different port
python manage.py runserver 0.0.0.0:8001
```

### Database Connection Error
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432 -U floor_user

# Restart PostgreSQL (if needed)
sudo service postgresql restart
```

### Redis Connection Error
```bash
# Check Redis status
redis-cli ping

# Should return: PONG
```

### Reset Database
```bash
# Drop all tables and recreate
python manage.py flush --noinput
python manage.py migrate
python manage.py createsuperuser
```

## Codespace Management

### Stop Codespace
- Click the Codespaces menu (bottom left in VS Code)
- Select **Stop Current Codespace**

### Delete Codespace
```bash
gh codespace delete
```

### List Codespaces
```bash
gh codespace list
```

## Performance Tips

1. **Use Port Forwarding**: Codespaces automatically forwards ports 8000, 5432, 6379
2. **Keep it Running**: Codespaces auto-stop after 30 minutes of inactivity
3. **Use VS Code Desktop**: Connect to Codespace from VS Code for better performance
4. **Prebuild**: Repository has devcontainer configuration for faster startup

## Support

If you encounter issues:
1. Check the **Output** panel in VS Code
2. Look at `.devcontainer/postCreateCommand.sh` logs
3. Open a new issue on GitHub with error details

## What's Next?

After Codespace is running:
- ✅ Test custom color system
- ✅ Explore dashboard visualizations  
- ✅ Try keyboard shortcuts
- ✅ Test AJAX filtering
- ✅ Review API documentation at /api/docs/
- ✅ Customize your theme preferences

Happy coding! 🚀

# GitHub Codespaces Configuration for Floor Management System

This directory contains the configuration for developing the Floor Management System in GitHub Codespaces.

## 🚀 Quick Start

1. **Open in Codespaces**: Click the "Code" button on GitHub and select "Create codespace on [branch-name]"
2. **Wait for setup**: The environment will automatically set up (this takes 2-3 minutes on first run)
3. **Start the server**: Run `python manage.py runserver` in the terminal
4. **Access the app**: Click on the "Ports" tab and open the forwarded port 8000

## 🔑 Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

## 📦 What's Included

### Services
- **Python 3.11**: Latest stable Python version
- **PostgreSQL 15**: Production-grade database
- **Django 5.2.6**: Web framework with all project dependencies

### VS Code Extensions
- Python (with Pylance and IntelliSense)
- Django support
- PostgreSQL tools
- Auto-formatting (Black)
- Import sorting (isort)

### Environment Variables
All necessary environment variables are automatically configured in the `.env` file created during setup.

## 🛠️ Development Workflow

### Running the Development Server
```bash
python manage.py runserver
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access database shell
python manage.py dbshell
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test <app_name>
```

### Creating a Superuser
```bash
python manage.py createsuperuser
```

## 🗄️ Database Access

The PostgreSQL database is accessible at:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `floor_mgmt_db`
- **User**: `postgres`
- **Password**: `postgres`

You can connect using the SQLTools extension in VS Code or via command line:
```bash
psql -h localhost -U postgres -d floor_mgmt_db
```

## 🔧 Customization

### Modifying the Environment

Edit the following files to customize your Codespace:
- `devcontainer.json`: VS Code settings and extensions
- `docker-compose.yml`: Service configuration
- `Dockerfile`: Base image and system dependencies
- `setup.sh`: Post-creation setup script

### Rebuilding the Container

If you make changes to the devcontainer configuration:
1. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Run "Codespaces: Rebuild Container"

## 📝 Template Testing

To test Django templates in Codespaces:

1. Make changes to templates in the project
2. Refresh the browser to see changes (Django auto-reloads)
3. Check the terminal for any template errors
4. Use Django Debug Toolbar for template debugging (if enabled)

## 🐛 Troubleshooting

### Database Connection Issues
If you encounter database connection errors:
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Restart the Codespace if needed
```

### Port Forwarding Issues
- Check the "Ports" tab in VS Code
- Ensure port 8000 is forwarded
- Make the port public if you need to share it

### Migration Issues
```bash
# Reset migrations (⚠️ destructive - development only)
python manage.py migrate --fake <app_name> zero
python manage.py migrate <app_name>
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)

## 🔒 Security Notes

⚠️ **Important**: The credentials and secret keys in this configuration are for development only. Never use these in production!

- Change `SECRET_KEY` in production
- Use strong passwords for database
- Configure proper `ALLOWED_HOSTS` for production
- Enable HTTPS in production environments

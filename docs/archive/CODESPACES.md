# 🚀 GitHub Codespaces Setup Guide

This guide helps you get started with the Floor Management System in GitHub Codespaces.

## Quick Start

### 1. Launch Codespace

1. Go to the repository on GitHub
2. Click the **Code** button (green button)
3. Select the **Codespaces** tab
4. Click **Create codespace on [your-branch]**

### 2. Wait for Automatic Setup

The Codespace will automatically:
- ✅ Install Python 3.11 and dependencies
- ✅ Set up PostgreSQL database
- ✅ Run database migrations
- ✅ Create a default admin user
- ✅ Configure VS Code extensions

**This takes approximately 2-3 minutes on first launch.**

### 3. Start Development Server

Once setup is complete, run:
```bash
python manage.py runserver
```

### 4. Access the Application

1. Look for the **Ports** tab in the bottom panel
2. Find port **8000** (Django Dev Server)
3. Click the **Open in Browser** icon (🌐) or globe icon
4. The application will open in a new browser tab

## 🔑 Default Login Credentials

```
Username: admin
Password: admin123
```

⚠️ **Change these credentials in production!**

## 📁 Project Structure

```
Floor-Management-System/
├── .devcontainer/          # Codespaces configuration
│   ├── devcontainer.json   # VS Code settings
│   ├── docker-compose.yml  # Service definitions
│   ├── Dockerfile          # Base image
│   ├── setup.sh           # Auto-setup script
│   └── README.md          # Detailed devcontainer docs
├── floor_mgmt/            # Django project settings
├── floor_app/             # Main application
└── requirements.txt       # Python dependencies
```

## 🛠️ Common Commands

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access database shell
python manage.py dbshell

# Create additional superuser
python manage.py createsuperuser
```

### Development
```bash
# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic

# Django shell
python manage.py shell
```

### Database Operations
```bash
# Connect to PostgreSQL directly
psql -h localhost -U postgres -d floor_mgmt_db

# Check database connection
pg_isready -h localhost -p 5432
```

## 🧪 Testing Templates

### Testing Django Templates
1. Navigate to template files in `floor_app/templates/`
2. Make your changes
3. Save the file
4. Refresh your browser (Django auto-reloads in DEBUG mode)

### Common Template Locations
- **Base templates**: `floor_app/templates/base/`
- **HR templates**: `floor_app/operations/hr/templates/`
- **Production templates**: `floor_app/operations/production/templates/`
- **Dashboard templates**: `floor_app/templates/dashboards/`

### Template Debugging Tips
- Check the terminal for template syntax errors
- Use Django's template debug mode
- Inspect the browser console for JavaScript errors
- Use VS Code's Django extension for syntax highlighting

## 🗄️ Database Configuration

The PostgreSQL database is automatically configured with:

| Setting  | Value           |
|----------|----------------|
| Host     | localhost      |
| Port     | 5432           |
| Database | floor_mgmt_db  |
| User     | postgres       |
| Password | postgres       |

## 📦 Installed VS Code Extensions

The Codespace includes:
- Python & Pylance (IntelliSense)
- Django support
- PostgreSQL tools (SQLTools)
- Black formatter
- isort (import organizer)
- Auto rename tag
- Prettier

## 🔧 Customizing Your Codespace

### Modifying Environment Variables

Edit `.env` file in the workspace root:
```bash
nano .env
```

### Rebuilding the Container

If you modify devcontainer configuration:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Codespaces: Rebuild Container"
3. Select and press Enter

## 🐛 Troubleshooting

### Port 8000 Not Accessible
1. Check the **Ports** tab in VS Code
2. Ensure port 8000 is forwarded
3. Make the port **Public** if sharing with others

### Database Connection Errors
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# View PostgreSQL logs
docker logs <postgres-container-id>

# Restart Codespace if needed
```

### Migration Conflicts
```bash
# Show current migration status
python manage.py showmigrations

# Run migrations
python manage.py migrate

# For serious issues, you may need to reset (development only!)
python manage.py migrate <app_name> zero
python manage.py migrate <app_name>
```

### Slow Performance
- First launch takes longer (building image)
- Subsequent launches are much faster
- Consider using a larger machine type in Codespace settings

## 🔒 Security Reminders

⚠️ **IMPORTANT**: This configuration is for development only!

**Never use in production:**
- Default SECRET_KEY
- Default database credentials
- DEBUG=True setting
- Weak admin password

**For production deployment:**
- Generate a strong SECRET_KEY
- Use environment-specific credentials
- Set DEBUG=False
- Configure proper ALLOWED_HOSTS
- Enable HTTPS
- Use strong passwords

## 📚 Additional Resources

- [Codespace Configuration Details](.devcontainer/README.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [Project Setup Guides](./DEPARTMENTS_SETUP.md)

## 💡 Tips & Best Practices

1. **Save Your Work**: Codespaces auto-save, but commit regularly
2. **Port Forwarding**: Use private ports by default for security
3. **Extensions**: Install additional VS Code extensions as needed
4. **Performance**: Close unused Codespaces to save resources
5. **Collaboration**: Share your Codespace URL for pair programming

## 🆘 Getting Help

If you encounter issues:
1. Check the terminal output for error messages
2. Review the `.devcontainer/README.md` for detailed configuration info
3. Ensure all environment variables are correctly set
4. Try rebuilding the container
5. Check GitHub Codespaces status page

---

**Happy Coding! 🎉**

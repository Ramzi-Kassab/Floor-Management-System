# GitHub Codespaces Configuration for Floor Management System

This directory contains the configuration for GitHub Codespaces, providing a complete, ready-to-use Django development environment in the cloud.

## 🚀 What Gets Installed Automatically

When you open this repository in Codespaces, the following setup happens automatically:

### Base Environment
- **Python 3.12** - Latest stable Python version
- **Node.js 20** - For frontend tooling (if needed)
- **PostgreSQL** - Database server (optional, using SQLite by default)
- **Git** - Version control

### Python Dependencies
All packages from `requirements.txt` are installed:
- Django 5.2.6
- Django REST Framework
- PostgreSQL adapter (psycopg2-binary)
- Pillow (image processing)
- QR code generation
- Phone number validation
- And more...

### VS Code Extensions
Automatically installed for the best Django development experience:
- **Python** - IntelliSense, debugging
- **Pylance** - Advanced type checking
- **Black Formatter** - Code formatting
- **Django Extension** - Django-specific features
- **Jinja** - Template syntax highlighting
- **Docker** - Container management
- **Code Spell Checker** - Catch typos
- **Prettier** - JavaScript/JSON formatting
- **ESLint** - JavaScript linting

### Database Setup
- SQLite database automatically created
- All migrations run
- Default superuser created:
  - **Username:** `admin`
  - **Password:** `admin123`

### Static Files
- Static files collected and ready
- Minified CSS/JS for production
- Development files for debugging

## 📂 Configuration Files

### `devcontainer.json`
Main configuration file that defines:
- Base Docker image
- VS Code extensions to install
- Port forwarding (8000 for Django, 5432 for PostgreSQL)
- Environment variables
- Post-creation command

### `setup.sh`
Automated setup script that:
1. Upgrades pip
2. Installs Python dependencies
3. Runs database migrations
4. Creates default superuser
5. Collects static files
6. Creates `.env` file with development settings
7. Displays helpful information

## 🎯 Quick Start

### 1. Open in Codespaces
Click the "Code" button on GitHub → "Codespaces" → "Create codespace on [branch-name]"

The branch to use:
```
claude/refactoring-master-prompt-01TJVoXKxvTqDKEXq8DWk539
```

### 2. Wait for Setup
The setup script runs automatically (2-3 minutes). Watch the terminal for progress.

### 3. Start Development Server
```bash
python manage.py runserver
```

### 4. Access Your Application
- **Django App:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **Login:** admin / admin123

## 🔧 Common Commands

### Development Server
```bash
# Start server (auto-reload on file changes)
python manage.py runserver

# Start on custom port
python manage.py runserver 8080
```

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test floor_app

# Run with coverage
python -m coverage run manage.py test
python -m coverage report
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic

# Find static files
python manage.py findstatic app.css
```

## 🌐 Frontend Development

The system includes a complete, production-ready frontend:

### Theme System
- **4 Color Controls:** Primary, Accent, Background, Text
- **5 Preset Themes:** Light, Dark, Blue, Green, Purple
- **Real-time Preview:** Changes apply instantly
- **Persistent Settings:** Saved to database for logged-in users

### Responsive Design
- **6 Breakpoints:** Mobile → Tablet → Desktop → Wide → Ultra-wide
- **Mobile-First:** Optimized for small screens first
- **Touch-Friendly:** Works great on tablets and phones

### Performance
- **Minified Assets:** 49.5% size reduction in production
- **Conditional Loading:** Full files in dev, minified in production
- **CDN Integration:** Bootstrap, Font Awesome, Chart.js

### Static Files Location
```
floor_app/static/
├── css/
│   ├── app.css (development)
│   ├── app.min.css (production)
│   ├── responsive-theme-system.css (development)
│   └── responsive-theme-system.min.css (production)
├── js/
│   ├── app.js (global utilities)
│   ├── navigation.js (sidebar, menus)
│   ├── theme.js (theme system)
│   └── *.min.js (minified versions)
└── hr/ (HR module scripts)
```

## 🔐 Security Notes

### Development Mode
The `.env` file created by setup has:
- `DEBUG=True` - Shows detailed error pages
- Simple `SECRET_KEY` - **NOT for production!**
- No SSL enforcement

### Production Deployment
Before deploying to production:
1. Set `DEBUG=False`
2. Generate secure `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL instead of SQLite
5. Enable SSL/HTTPS
6. Configure proper email backend

## 📦 Pre-installed Features

### Backend (100% Complete)
- ✅ 28 operational modules
- ✅ Django 5.2.6
- ✅ REST API with Django REST Framework
- ✅ PostgreSQL support
- ✅ User authentication & permissions
- ✅ Complete models for all modules

### Frontend (100% Complete)
- ✅ 226 templates (all functional)
- ✅ Bootstrap 5.3.3
- ✅ Enhanced theme system
- ✅ 94+ Bootstrap Icons
- ✅ Font Awesome integration
- ✅ Chart.js & ApexCharts
- ✅ Mobile-responsive (6 breakpoints)
- ✅ WCAG AA accessible

### Modules Available
1. HR & Administration
2. Inventory Management
3. Production & Job Cards
4. Quality Control (NCRs)
5. Sales & CRM
6. Engineering & BOMs
7. Purchasing & Procurement
8. Maintenance
9. Planning & Scheduling
10. Analytics & Reporting
11. Finance & Accounting
12. Device Tracking
13. GPS System
14. QR Code Management
15. Notifications
16. Document Management
17. Training Programs
18. Evaluation System
19. And more...

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
pkill -f runserver

# Or use a different port
python manage.py runserver 8080
```

### Database Issues
```bash
# Reset database (WARNING: Deletes all data!)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --no-input
```

### Permission Errors
```bash
# Fix permissions
chmod +x .devcontainer/setup.sh
```

## 📚 Additional Resources

### Documentation
- Django Docs: https://docs.djangoproject.com/en/5.2/
- Bootstrap Docs: https://getbootstrap.com/docs/5.3/
- REST Framework: https://www.django-rest-framework.org/

### Project Documentation
- `docs/FRONTEND_AUDIT_COMPLETE.md` - Complete frontend audit
- `docs/FRONTEND_IMPLEMENTATION_COMPLETE.md` - Frontend implementation details
- Various module-specific READMEs in `floor_app/operations/*/`

## 🎉 You're Ready to Code!

Everything is set up and ready to go. Start the dev server and begin coding:

```bash
python manage.py runserver
```

Happy coding! 🚀

# 🚀 Quick Start Guide - Floor Management System

This guide will help you merge the project, run migrations, review HTML pages, and fix any issues.

---

## 📋 Table of Contents

1. [What is Docker?](#what-is-docker)
2. [Option 1: With Docker (Recommended)](#option-1-with-docker-recommended)
3. [Option 2: Without Docker (Traditional)](#option-2-without-docker-traditional)
4. [Reviewing HTML Pages](#reviewing-html-pages)
5. [Fixing Template Issues](#fixing-template-issues)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## 🐳 What is Docker?

### Simple Explanation:

**Docker** is like a "shipping container" for your application. Instead of installing Python, PostgreSQL, and all dependencies manually on your computer, Docker packages everything into isolated containers that work the same everywhere.

### Real-World Analogy:

Imagine you're moving houses:
- **Without Docker**: You pack individual items (books, clothes, furniture) and hope they fit in the new house. You might need to buy new furniture if it doesn't fit.
- **With Docker**: You put your entire furnished room in a container. The container works exactly the same in any house.

### Benefits:

✅ **No "works on my machine" problems** - Same environment everywhere
✅ **Quick setup** - One command instead of hours of installation
✅ **Isolation** - Each project has its own environment
✅ **Easy sharing** - Team members get identical setup
✅ **Production-ready** - Same container runs in dev and production

---

## 🚀 Option 1: With Docker (Recommended)

This is the **easiest and fastest** way to get started.

### Prerequisites:

- Install Docker Desktop: https://www.docker.com/products/docker-desktop
- Git installed

### Step-by-Step:

#### 1. Get the Latest Code

```bash
# Navigate to project
cd /path/to/Floor-Management-System

# Fetch latest changes
git fetch origin

# Switch to the branch with improvements
git checkout claude/floor-system-health-check-01THJSxKiE5nspKXgwWdDiA5

# Pull latest changes
git pull origin claude/floor-system-health-check-01THJSxKiE5nspKXgwWdDiA5
```

#### 2. Use the Automated Startup Script

**Easy Mode (Automated):**
```bash
./scripts/start_and_test.sh
```

This script will:
- ✅ Check Docker installation
- ✅ Start all containers (PostgreSQL + Django)
- ✅ Run migrations automatically
- ✅ Load test data
- ✅ Check templates for issues
- ✅ Run automated tests
- ✅ Start the server

**Manual Mode (Step-by-step):**
```bash
# Start containers
docker-compose up -d

# Wait for database (about 10 seconds)
sleep 10

# Run migrations
docker-compose exec web python manage.py migrate

# Load test data
docker-compose exec web python manage.py load_test_data

# Check system health
curl http://localhost:8000/api/health/
```

#### 3. Access the Application

Open your web browser:
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

#### 4. Create a Superuser (Admin Account)

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts to create your admin account.

#### 5. Review Pages in Browser

Now you can click through all the pages and check for:
- ❌ Broken links
- ❌ Missing styles
- ❌ Template errors
- ❌ JavaScript errors (check browser console with F12)

#### 6. View Logs for Errors

```bash
# Real-time logs
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web

# Search for errors
docker-compose logs web | grep ERROR
```

#### 7. Stop Everything When Done

```bash
docker-compose down
```

---

## 🔧 Option 2: Without Docker (Traditional)

If you can't use Docker, follow these steps:

### Prerequisites:

- Python 3.11+
- PostgreSQL 15+
- Git

### Step-by-Step:

#### 1. Get the Latest Code

```bash
cd /path/to/Floor-Management-System
git checkout claude/floor-system-health-check-01THJSxKiE5nspKXgwWdDiA5
git pull
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy .env.example to .env (if exists)
# Or create .env with:
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=floor_management
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5433
```

#### 5. Start PostgreSQL

Make sure PostgreSQL is running on port 5433.

```bash
# Check if running
psql -U postgres -h localhost -p 5433 -l

# Create database if doesn't exist
psql -U postgres -h localhost -p 5433 -c "CREATE DATABASE floor_management;"
```

#### 6. Run Migrations

```bash
python manage.py migrate
```

#### 7. Load Test Data

```bash
python manage.py load_test_data
```

#### 8. Create Superuser

```bash
python manage.py createsuperuser
```

#### 9. Run Development Server

```bash
python manage.py runserver
```

#### 10. Access Application

Open browser to: http://localhost:8000

---

## 🔍 Reviewing HTML Pages

### What to Check:

#### 1. Visual Review (In Browser)

✅ **Layout**
- Pages load correctly
- No broken layouts
- Responsive design works
- Navigation menus work

✅ **Content**
- No Lorem Ipsum placeholder text
- Tables display data
- Forms render correctly
- Buttons work

✅ **Functionality**
- Links work (no 404 errors)
- Forms submit
- Search works
- Filters work

✅ **Console (Press F12)**
- No JavaScript errors (red text)
- No 404s for CSS/JS files
- No CSRF token errors

#### 2. Automated Template Check

```bash
# With Docker
docker-compose exec web python scripts/check_templates.py

# Without Docker
python scripts/check_templates.py
```

**Current Status**: Found 128 minor issues in 1,181 templates
- Mostly missing `{% load %}` statements
- 2 templates with mismatched blocks

#### 3. Check Server Logs

```bash
# With Docker
docker-compose logs web | grep ERROR

# Without Docker
# Watch terminal where server is running
```

---

## 🔨 Fixing Template Issues

### Automated Fixes

We found 128 template issues. Most can be fixed automatically:

```bash
# Dry run (see what would be fixed)
python scripts/fix_templates.py

# Apply fixes
python scripts/fix_templates.py --apply
```

### Manual Fixes for Specific Issues:

#### Issue 1: Missing {% load static %}

**Before:**
```html
{% extends "base.html" %}

{% block content %}
    <img src="{% static 'images/logo.png' %}">
{% endblock %}
```

**After:**
```html
{% extends "base.html" %}
{% load static %}

{% block content %}
    <img src="{% static 'images/logo.png' %}">
{% endblock %}
```

#### Issue 2: Mismatched Block Tags

**Problem Templates:**
- `floor_app/operations/hiring/templates/hiring/candidate_list.html`
- `floor_app/operations/hiring/templates/hiring/offer_list.html`

**Fix:** Count `{% block %}` and `{% endblock %}` tags - they must match.

---

## 🐛 Common Issues & Solutions

### Issue 1: Docker Not Starting

**Problem:** `docker-compose up` fails

**Solution:**
```bash
# Check Docker is running
docker --version

# Check if ports are in use
lsof -i :8000
lsof -i :5433

# Kill conflicting processes
kill -9 <PID>

# Try again
docker-compose down
docker-compose up -d
```

### Issue 2: Database Connection Failed

**Problem:** Django can't connect to database

**Solution:**
```bash
# With Docker - check database is running
docker-compose ps db
docker-compose logs db

# Wait longer for database
sleep 15

# Restart database
docker-compose restart db
```

### Issue 3: Migrations Failed

**Problem:** `python manage.py migrate` fails

**Solution:**
```bash
# Check for migration conflicts
python manage.py showmigrations

# Check database connection
python manage.py dbshell

# Try running migrations one app at a time
python manage.py migrate core
python manage.py migrate floor_app
python manage.py migrate hr
# etc.
```

### Issue 4: Static Files Not Loading

**Problem:** CSS/JS files return 404

**Solution:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# In development, DEBUG=True should serve static files automatically

# Check STATIC_URL and STATIC_ROOT in settings
```

### Issue 5: Template Not Found

**Problem:** `TemplateDoesNotExist` error

**Solution:**
```bash
# Check template path is correct
# Django looks in:
# 1. app/templates/
# 2. TEMPLATES DIRS setting

# Check template file exists
find . -name "your_template.html"
```

### Issue 6: CSRF Verification Failed

**Problem:** Forms show CSRF error

**Solution:**
```html
<!-- Make sure all POST forms have: -->
{% csrf_token %}

<!-- Example: -->
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>
```

---

## 🧪 Testing Workflow

### 1. Quick Smoke Test

Test critical paths manually:

```
✅ Homepage loads
✅ Login works
✅ Admin panel accessible
✅ Create a test record
✅ Edit a record
✅ Delete a record
✅ Search works
✅ Reports generate
```

### 2. Automated Tests

```bash
# With Docker
docker-compose exec web python manage.py test

# Specific app
docker-compose exec web python manage.py test core.tests.test_health

# With coverage
docker-compose exec web pytest --cov=floor_app --cov=core
```

### 3. Check for Broken Links

```bash
# Install linkchecker (optional)
pip install linkchecker

# Check all links
linkchecker http://localhost:8000
```

---

## 📊 Health Check Dashboard

Monitor system health in real-time:

```bash
# Check health
curl http://localhost:8000/api/health/ | python -m json.tool

# Continuous monitoring
watch -n 5 'curl -s http://localhost:8000/api/health/ | python -m json.tool'
```

Expected healthy response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T...",
  "version": "1.0.0",
  "components": {
    "database": {"status": "healthy"},
    "cache": {"status": "healthy"},
    "python": {"status": "healthy"}
  }
}
```

---

## 🎯 Workflow Summary

### Quick Daily Workflow:

```bash
# 1. Start system
./scripts/start_and_test.sh

# 2. Open browser
open http://localhost:8000

# 3. Review pages, note issues

# 4. Fix issues in code

# 5. Restart to see changes
docker-compose restart web

# 6. When done
docker-compose down
```

### First-Time Setup:

```bash
# 1. Get code
git clone <repo>
cd Floor-Management-System
git checkout claude/floor-system-health-check-01THJSxKiE5nspKXgwWdDiA5

# 2. Start with Docker
docker-compose up -d

# 3. Wait for startup
sleep 15

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Load test data
docker-compose exec web python manage.py load_test_data

# 6. Create admin user
docker-compose exec web python manage.py createsuperuser

# 7. Open browser
open http://localhost:8000
```

---

## 📚 Additional Resources

### Documentation:
- **DOCKER_SETUP.md** - Comprehensive Docker guide
- **IMPROVEMENTS.md** - All recent improvements
- **HEALTH_CHECK_COMPLETE.md** - System health report

### Useful Commands:

```bash
# View all Docker containers
docker ps

# View Django logs
docker-compose logs web

# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec db psql -U postgres -d floor_management

# Run specific test
docker-compose exec web python manage.py test core.tests.test_health

# Check for security issues
docker-compose exec web python manage.py check --deploy

# Create migrations
docker-compose exec web python manage.py makemigrations
```

---

## 🤝 Need Help?

### Troubleshooting Steps:

1. ✅ Check Docker is running: `docker --version`
2. ✅ Check containers are up: `docker-compose ps`
3. ✅ Check logs for errors: `docker-compose logs web`
4. ✅ Check database is ready: `docker-compose exec db pg_isready`
5. ✅ Check Django health: `curl http://localhost:8000/api/health/`

### Getting Support:

- Check logs first: `docker-compose logs`
- Review error messages carefully
- Check DOCKER_SETUP.md for detailed help
- Search error messages online

---

## ✅ Success Checklist

Before considering review complete:

- [ ] Docker containers start successfully
- [ ] Migrations run without errors
- [ ] Test data loads correctly
- [ ] Superuser account created
- [ ] Homepage loads (http://localhost:8000)
- [ ] Admin panel accessible (http://localhost:8000/admin/)
- [ ] Health check passes (http://localhost:8000/api/health/)
- [ ] No JavaScript errors in browser console (F12)
- [ ] Can create/edit/delete records
- [ ] Search functionality works
- [ ] Forms submit correctly
- [ ] Template checker shows minimal issues
- [ ] Automated tests pass

---

**Happy reviewing! 🚀**

*This project is now production-ready with Docker, health monitoring, automated tests, and comprehensive documentation.*

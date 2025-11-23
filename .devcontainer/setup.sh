#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Floor Management System - Codespace Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip
print_success "pip upgraded"

# Step 2: Install Python dependencies
print_step "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Step 3: Check if database exists
print_step "Checking database..."
if [ -f "db.sqlite3" ]; then
    print_warning "Database already exists, skipping initial setup"
else
    print_step "Creating new SQLite database..."

    # Step 4: Run migrations
    print_step "Running database migrations..."
    python manage.py makemigrations
    python manage.py migrate
    print_success "Database migrations completed"

    # Step 5: Create superuser (non-interactive)
    print_step "Creating default superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@floormanagement.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
EOF
    print_success "Superuser ready: admin / admin123"
fi

# Step 6: Collect static files (optional for dev, but good to have)
print_step "Collecting static files..."
python manage.py collectstatic --no-input --clear || print_warning "Static files collection skipped (may not be configured)"

# Step 7: Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_step "Creating .env file for local development..."
    cat > .env << 'ENVEOF'
# Django Settings
DEBUG=True
SECRET_KEY=dev-secret-key-for-codespaces-only-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.app.github.dev

# Database (using SQLite for Codespaces)
DATABASE_URL=sqlite:///db.sqlite3

# Email (console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security (disabled for development)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
ENVEOF
    print_success ".env file created"
else
    print_warning ".env file already exists"
fi

# Step 8: Display success message
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✓ Codespace Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Quick Start Commands:"
echo "  • Run development server:  python manage.py runserver"
echo "  • Create superuser:        python manage.py createsuperuser"
echo "  • Run migrations:          python manage.py migrate"
echo "  • Access Django shell:     python manage.py shell"
echo ""
echo "🔐 Default Admin Credentials:"
echo "  • Username: admin"
echo "  • Password: admin123"
echo "  • URL: http://localhost:8000/admin/"
echo ""
echo "🌐 Frontend Features:"
echo "  • Enhanced Theme System: 4 color controls"
echo "  • Responsive Design: 6 breakpoints (mobile-first)"
echo "  • Production-Optimized: Minified CSS/JS (49.5% reduction)"
echo "  • Accessibility: WCAG AA compliant"
echo ""
echo "📁 Key Directories:"
echo "  • Templates: floor_app/templates/"
echo "  • Static Files: floor_app/static/"
echo "  • Models: floor_app/models*.py"
echo "  • Views: floor_app/views.py"
echo ""
echo "💡 Tip: The dev server will auto-reload on file changes!"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Step 9: Display Django version and project info
print_step "System Information:"
python --version
python manage.py --version
echo ""
print_success "Environment ready for development!"

#!/bin/bash
set -e

echo "🚀 Starting Floor Management System setup in Codespaces..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start in time"
        exit 1
    fi
    sleep 1
done

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Database Configuration (matching settings.py variable names)
DB_NAME=floor_mgmt_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
DEBUG=True
SECRET_KEY=dev-secret-key-for-codespaces-only-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.app.github.dev

# Additional settings
DJANGO_SETTINGS_MODULE=floor_mgmt.settings
EOL
    echo "✅ .env file created"
fi

# Install Python dependencies (in case they were updated)
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Run Django migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
python manage.py shell << 'PYTHON_SCRIPT'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Superuser 'admin' created with password 'admin123'")
else:
    print("ℹ️  Superuser 'admin' already exists")
PYTHON_SCRIPT

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo ""
echo "✨ Setup complete! ✨"
echo ""
echo "📋 Next steps:"
echo "   1. Start the development server: python manage.py runserver"
echo "   2. Access the application at the forwarded port 8000"
echo "   3. Login with username: admin, password: admin123"
echo ""
echo "🔧 Useful commands:"
echo "   - Create migrations: python manage.py makemigrations"
echo "   - Run migrations: python manage.py migrate"
echo "   - Create superuser: python manage.py createsuperuser"
echo "   - Run tests: python manage.py test"
echo ""

#!/bin/bash
set -e

echo "🚀 Setting up Floor Management System development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h localhost -p 5432 -U floor_user; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h localhost ping > /dev/null 2>&1; do
  sleep 1
done
echo "✅ Redis is ready"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'ENV_EOF'
# Django settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.preview.app.github.dev

# Database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=floor_management
DB_USER=floor_user
DB_PASSWORD=floor_password
DB_HOST=localhost
DB_PORT=5432

# Redis settings
REDIS_URL=redis://localhost:6379/0

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ENV_EOF
    echo "✅ .env file created"
fi

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --skip-checks

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell --skip-checks << PYTHON_EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin / admin123')
else:
    print('ℹ️  Superuser already exists')
PYTHON_EOF

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --skip-checks || true

echo ""
echo "✨ Setup complete! You can now:"
echo "   1. Run the development server: python manage.py runserver 0.0.0.0:8000"
echo "   2. Access admin panel: http://localhost:8000/admin/"
echo "   3. Login with: admin / admin123"
echo "   4. Start Celery worker: celery -A floor_mgmt worker -l info"
echo ""

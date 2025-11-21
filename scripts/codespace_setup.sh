#!/bin/bash

# GitHub Codespaces automatic setup script
# This runs when the Codespace starts

echo "🚀 Setting up Floor Management System in GitHub Codespaces..."
echo ""

# Start Docker Compose
echo "📦 Starting Docker containers..."
docker-compose up -d

# Wait for database
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec -T web python manage.py migrate

# Load test data
echo "📊 Loading test data..."
docker-compose exec -T web python manage.py load_test_data || echo "⚠️  Test data already loaded or error occurred"

# Check templates
echo "🔍 Checking templates..."
docker-compose exec -T web python scripts/check_templates.py | head -50

# Show success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Your Django application is running!"
echo "   Click on the 'Ports' tab below and open port 8000"
echo "   Or use the notification popup to open the URL"
echo ""
echo "🔧 Useful commands:"
echo "   docker-compose logs -f web           # View logs"
echo "   docker-compose exec web python manage.py shell    # Django shell"
echo "   docker-compose exec web python manage.py createsuperuser  # Create admin"
echo ""
echo "📚 Documentation:"
echo "   See QUICK_START_GUIDE.md for more information"
echo ""

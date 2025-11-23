#!/bin/bash
# Floor Management System - Deployment Script

set -e  # Exit on error

echo "================================"
echo "Floor Management System Deployment"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Activate with: source venv/bin/activate"
    exit 1
fi

echo -e "${GREEN}✓${NC} Virtual environment active"

# Pull latest changes
echo ""
echo "Pulling latest changes from git..."
git pull origin master
echo -e "${GREEN}✓${NC} Git pull completed"

# Install/Update dependencies
echo ""
echo "Installing/Updating dependencies..."
pip install -r requirements.txt --upgrade
echo -e "${GREEN}✓${NC} Dependencies updated"

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✓${NC} Static files collected"

# Run database migrations
echo ""
echo "Running database migrations..."
python manage.py migrate --noinput
echo -e "${GREEN}✓${NC} Migrations completed"

# Run deployment checks
echo ""
echo "Running deployment checks..."
python manage.py check --deploy
python manage.py check_deployment
echo -e "${GREEN}✓${NC} Deployment checks passed"

# Restart application (systemd)
echo ""
echo "Restarting application..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart floor-mgmt
    sudo systemctl status floor-mgmt --no-pager
    echo -e "${GREEN}✓${NC} Application restarted"
else
    echo -e "${YELLOW}Warning: systemctl not found. Please restart manually.${NC}"
fi

# Clear cache (if using Redis/Memcached)
echo ""
echo "Clearing cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
echo -e "${GREEN}✓${NC} Cache cleared"

echo ""
echo "================================"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "================================"

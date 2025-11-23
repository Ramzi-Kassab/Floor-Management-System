#!/bin/bash
# Floor Management System - Initial Setup Script

set -e  # Exit on error

echo "================================"
echo "Floor Management System Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "Python version: $PYTHON_VERSION"
    if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
        echo -e "${YELLOW}Warning: Python 3.10+ recommended${NC}"
    else
        echo -e "${GREEN}✓${NC} Python version OK"
    fi
else
    echo "Python 3 not found!"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip
echo -e "${GREEN}✓${NC} Pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Copy environment file if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}Warning: Please update .env with your configuration${NC}"
else
    echo ".env file already exists"
fi

# Check PostgreSQL
echo ""
echo "Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL client found"
else
    echo -e "${YELLOW}Warning: PostgreSQL client not found${NC}"
    echo "Install with: sudo apt-get install postgresql-client"
fi

# Create database (optional)
echo ""
read -p "Create database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter database name [floor_mgmt_db]: " DB_NAME
    DB_NAME=${DB_NAME:-floor_mgmt_db}
    createdb $DB_NAME || echo "Database may already exist"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py migrate
echo -e "${GREEN}✓${NC} Migrations completed"

# Create superuser
echo ""
read -p "Create superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Generate test data (optional)
echo ""
read -p "Generate test data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Dataset size (minimal/standard/large) [standard]: " SIZE
    SIZE=${SIZE:-standard}
    python manage.py generate_test_data --size=$SIZE
    echo -e "${GREEN}✓${NC} Test data generated"
fi

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✓${NC} Static files collected"

echo ""
echo "================================"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "================================"
echo ""
echo "To start the development server:"
echo "  python manage.py runserver"
echo ""
echo "Access the application at:"
echo "  http://localhost:8000"
echo ""
echo "Admin interface:"
echo "  http://localhost:8000/admin"
echo ""

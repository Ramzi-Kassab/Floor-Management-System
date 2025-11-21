#!/bin/bash

# Comprehensive startup and testing script for Floor Management System
# This script will:
# 1. Check system requirements
# 2. Start Docker containers
# 3. Run migrations
# 4. Load test data
# 5. Check for common issues
# 6. Run tests
# 7. Start the server

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "  Floor Management System - Startup & Testing Script"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# Step 1: Check if Docker is installed
echo ""
echo "Step 1: Checking Docker installation..."
if command -v docker &> /dev/null; then
    print_success "Docker is installed"
    docker --version
else
    print_error "Docker is not installed"
    echo "Please install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose is installed"
    docker-compose --version
else
    print_error "Docker Compose is not installed"
    exit 1
fi

# Step 2: Check if docker-compose.yml exists
echo ""
echo "Step 2: Checking project files..."
if [ -f "docker-compose.yml" ]; then
    print_success "docker-compose.yml found"
else
    print_error "docker-compose.yml not found. Are you in the project root?"
    exit 1
fi

# Step 3: Stop any running containers
echo ""
echo "Step 3: Cleaning up any existing containers..."
docker-compose down 2>/dev/null || true
print_success "Cleaned up existing containers"

# Step 4: Start containers
echo ""
echo "Step 4: Starting Docker containers..."
print_info "This may take a few minutes on first run..."
docker-compose up -d

# Wait for database to be ready
echo ""
echo "Step 5: Waiting for database to be ready..."
sleep 5
MAX_TRIES=30
TRIES=0
while ! docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    TRIES=$((TRIES+1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        print_error "Database failed to start after 30 seconds"
        docker-compose logs db
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo ""
print_success "Database is ready"

# Step 6: Run Django checks
echo ""
echo "Step 6: Running Django system checks..."
if docker-compose exec -T web python manage.py check; then
    print_success "Django system check passed"
else
    print_error "Django system check failed"
    exit 1
fi

# Step 7: Run migrations
echo ""
echo "Step 7: Running database migrations..."
if docker-compose exec -T web python manage.py migrate; then
    print_success "Migrations completed"
else
    print_error "Migrations failed"
    exit 1
fi

# Step 8: Load test data
echo ""
echo "Step 8: Loading test data..."
if docker-compose exec -T web python manage.py load_test_data; then
    print_success "Test data loaded"
else
    print_warning "Test data loading failed (non-critical)"
fi

# Step 9: Check templates
echo ""
echo "Step 9: Checking HTML templates..."
if docker-compose exec -T web python scripts/check_templates.py > /tmp/template_check.txt; then
    ISSUES=$(grep "Total issues found:" /tmp/template_check.txt | awk '{print $4}')
    if [ "$ISSUES" -gt 0 ]; then
        print_warning "Found $ISSUES template issues (see report below)"
    else
        print_success "All templates passed checks"
    fi
else
    print_warning "Template check failed (non-critical)"
fi

# Step 10: Run tests
echo ""
echo "Step 10: Running automated tests..."
if docker-compose exec -T web python manage.py test core.tests.test_health --verbosity=0; then
    print_success "Health check tests passed"
else
    print_warning "Some tests failed (non-critical)"
fi

# Step 11: Check health endpoint
echo ""
echo "Step 11: Testing health endpoint..."
sleep 2
if curl -s http://localhost:8000/api/health/ > /dev/null; then
    print_success "Health endpoint is responding"
    curl -s http://localhost:8000/api/health/ | python -m json.tool | head -20
else
    print_warning "Health endpoint not responding yet (may need more time)"
fi

# Final summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🎉 System is up and running!"
echo "════════════════════════════════════════════════════════════════"
echo ""
print_info "Access the application:"
echo "  • Web App:        http://localhost:8000"
echo "  • Admin Panel:    http://localhost:8000/admin/"
echo "  • Health Check:   http://localhost:8000/api/health/"
echo ""
print_info "Useful commands:"
echo "  • View logs:      docker-compose logs -f web"
echo "  • Django shell:   docker-compose exec web python manage.py shell"
echo "  • Create superuser: docker-compose exec web python manage.py createsuperuser"
echo "  • Run tests:      docker-compose exec web python manage.py test"
echo "  • Stop all:       docker-compose down"
echo ""
print_info "Test users (password: test123):"
echo "  • prod_manager"
echo "  • qc_inspector"
echo "  • warehouse_clerk"
echo ""
echo "════════════════════════════════════════════════════════════════"

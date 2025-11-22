#!/bin/bash
#
# CORE APP EXPORT UTILITY - PHASE 2
# Creates a distributable package of the core app for easy deployment
#
# This script packages the core app including:
# - Models (core/models.py)
# - Context processors (core/context_processors.py)
# - Migrations
# - Documentation
# - Requirements
#
# Output: core_app_package_YYYYMMDD_HHMMSS.tar.gz
#
# Usage:
#   bash scripts/export_core_package.sh [OUTPUT_DIR]
#
# Example:
#   bash scripts/export_core_package.sh /tmp
#   bash scripts/export_core_package.sh ~/Downloads
#

set -e
set -o pipefail

# Color codes
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m'

# Script configuration
readonly SCRIPT_VERSION="1.0.0"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly PACKAGE_NAME="core_app_package_${TIMESTAMP}"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}║         CORE APP EXPORT UTILITY - PHASE 2             ║${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Determine output directory
if [ -z "$1" ]; then
    OUTPUT_DIR="/tmp"
else
    OUTPUT_DIR="$1"
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo -e "${YELLOW}!${NC} Output directory not found: $OUTPUT_DIR"
    echo -e "${BLUE}→${NC} Creating directory..."
    mkdir -p "$OUTPUT_DIR"
fi

echo -e "${BLUE}→${NC} Output directory: $OUTPUT_DIR"
echo ""

# Validate we're in the right repository
if [ ! -f "core/models.py" ]; then
    echo -e "${RED}✗${NC} Error: core/models.py not found"
    echo -e "${RED}✗${NC} Are you in the Floor-Management-System directory?"
    exit 1
fi

# Create temporary packaging directory
PACKAGE_DIR=$(mktemp -d)
CORE_DIR="$PACKAGE_DIR/$PACKAGE_NAME"
mkdir -p "$CORE_DIR"

echo -e "${BLUE}[1/7]${NC} Preparing package structure..."
mkdir -p "$CORE_DIR/core"
mkdir -p "$CORE_DIR/docs"
mkdir -p "$CORE_DIR/scripts"
echo -e "${GREEN}✓${NC} Package structure created"
echo ""

# Copy core app files
echo -e "${BLUE}[2/7]${NC} Copying core app files..."

# Copy core module
cp -r core/* "$CORE_DIR/core/"
MODEL_LINES=$(wc -l < core/models.py)
MODEL_COUNT=$(grep -c "^class.*models.Model" core/models.py || echo "0")
echo -e "${GREEN}✓${NC} Copied core app ($MODEL_COUNT models, $MODEL_LINES lines)"

# Copy documentation
if [ -f "docs/PHASE2_MIGRATION_PLAN.md" ]; then
    cp docs/PHASE2_MIGRATION_PLAN.md "$CORE_DIR/docs/"
    echo -e "${GREEN}✓${NC} Copied PHASE2_MIGRATION_PLAN.md"
fi

if [ -f "docs/PHASE_1_AUDIT.md" ]; then
    cp docs/PHASE_1_AUDIT.md "$CORE_DIR/docs/"
    echo -e "${GREEN}✓${NC} Copied PHASE_1_AUDIT.md"
fi

# Copy migration script
if [ -f "scripts/migrate_core_app.sh" ]; then
    cp scripts/migrate_core_app.sh "$CORE_DIR/scripts/"
    chmod +x "$CORE_DIR/scripts/migrate_core_app.sh"
    echo -e "${GREEN}✓${NC} Copied migration script"
fi

echo ""

# Create README for the package
echo -e "${BLUE}[3/7]${NC} Generating package README..."

cat > "$CORE_DIR/README.md" << 'EOF'
# Core App Package - Floor Management System

**Version:** 1.0.0
**Generated:** $(date +%Y-%m-%d)
**Source:** Floor-Management-System (Old Repo B)

## Contents

This package contains the complete core app from the Floor Management System, ready for migration to a new clean repository.

### Directory Structure

```
core_app_package_YYYYMMDD_HHMMSS/
├── core/                          # Core Django app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                  # 12 models, ~1,127 lines
│   ├── context_processors.py      # If present
│   ├── tests.py
│   ├── views.py
│   └── migrations/
│       └── 0001_initial.py        # Initial migration (if present)
├── docs/                          # Documentation
│   ├── PHASE2_MIGRATION_PLAN.md   # Complete migration strategy
│   └── PHASE_1_AUDIT.md           # Technical debt audit
├── scripts/                       # Utility scripts
│   └── migrate_core_app.sh        # Automated migration script
└── README.md                      # This file
```

## Models Included (12 total)

1. **UserPreference** - User UI preferences, themes, table settings
2. **CostCenter** - Financial tracking with hierarchy and budgets
3. **ERPDocumentType** - ERP document type definitions
4. **ERPReference** - Generic ERP integration mapping (uses GenericFK)
5. **LossOfSaleCause** - Loss of sale categorization
6. **LossOfSaleEvent** - Loss tracking with financial impact (uses GenericFK)
7. **ApprovalType** - Approval workflow type definitions
8. **ApprovalAuthority** - Approval routing configuration
9. **Currency** - Multi-currency master data
10. **ExchangeRate** - Foreign exchange rate tracking
11. **Notification** - User notification system (uses GenericFK)
12. **ActivityLog** - System-wide audit trail (uses GenericFK)

## Quick Start

### Option 1: Using the Automated Script

```bash
# Extract the package
tar -xzf core_app_package_YYYYMMDD_HHMMSS.tar.gz
cd core_app_package_YYYYMMDD_HHMMSS

# Run the migration script
bash scripts/migrate_core_app.sh /path/to/target/repo

# Follow the prompts
```

### Option 2: Manual Installation

```bash
# 1. Extract package
tar -xzf core_app_package_YYYYMMDD_HHMMSS.tar.gz
cd core_app_package_YYYYMMDD_HHMMSS

# 2. Copy core app to your Django project
cp -r core/ /path/to/your/django/project/

# 3. Update settings.py
# Add 'core' to INSTALLED_APPS:
#
#   INSTALLED_APPS = [
#       ...
#       'core',  # Foundation: shared utilities, cost centers, notifications
#   ]

# 4. Create migrations
cd /path/to/your/django/project
python manage.py makemigrations core

# 5. Run system check
python manage.py check

# 6. Apply migrations (requires database)
python manage.py migrate core

# 7. Test
python manage.py test core
```

## Dependencies

The core app requires:

- **Django:** >= 5.0
- **djangorestframework:** For API support
- **python-decouple:** For environment configuration
- **Database:** PostgreSQL recommended (SQLite for development)

Install with:
```bash
pip install django djangorestframework python-decouple psycopg2-binary
```

## Database Tables

The core app creates these database tables:

- `core_user_preference`
- `core_cost_center`
- `core_erp_document_type`
- `core_erp_reference`
- `core_loss_of_sale_cause`
- `core_loss_of_sale_event`
- `core_approval_type`
- `core_approval_authority`
- `core_currency`
- `core_exchange_rate`
- `core_notification`
- `core_activity_log`

## Important Notes

### GenericForeignKey Usage

Four models use Django's GenericForeignKey for flexible relationships:

- **ERPReference:** Can link to any model for ERP integration
- **LossOfSaleEvent:** Can link to JobCard, Asset, or other objects
- **Notification:** Can reference any object for contextual notifications
- **ActivityLog:** Tracks changes to any model type

Make sure `django.contrib.contenttypes` is in your INSTALLED_APPS.

### Context Processors

If `core/context_processors.py` is present, add to `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                # ... other context processors ...
                'core.context_processors.user_preferences',
                'core.context_processors.global_settings',
            ],
        },
    },
]
```

### Migration Strategy

This core app is part of Phase 2 migration from the old Floor Management System repository. See `docs/PHASE2_MIGRATION_PLAN.md` for:

- Complete migration timeline
- App dependencies
- Testing requirements
- Next apps to migrate (HR, Inventory, Engineering, etc.)

## Testing

```bash
# Run core app tests
python manage.py test core

# Run with verbosity
python manage.py test core --verbosity=2

# Run specific test
python manage.py test core.tests.TestUserPreference
```

## Support

For migration assistance or issues:

1. Review `docs/PHASE2_MIGRATION_PLAN.md` for detailed guidance
2. Check `docs/PHASE_1_AUDIT.md` for technical context
3. Use `scripts/migrate_core_app.sh` for automated migration

## Version History

- **1.0.0** (2025-11-22): Initial core app package
  - 12 models migrated
  - Complete documentation included
  - Automated migration script
  - Ready for Phase 2 deployment

---

**Generated by:** Floor Management System Migration Tools
**License:** As per main project
**Source Repository:** https://github.com/Ramzi-Kassab/Floor-Management-System
EOF

sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/" "$CORE_DIR/README.md"
sed -i "s/YYYYMMDD_HHMMSS/$TIMESTAMP/g" "$CORE_DIR/README.md"

echo -e "${GREEN}✓${NC} Package README created"
echo ""

# Create requirements.txt
echo -e "${BLUE}[4/7]${NC} Creating requirements.txt..."

cat > "$CORE_DIR/requirements.txt" << 'EOF'
# Core App Requirements - Floor Management System
# Generated for Phase 2 migration

# Django framework
Django>=5.0,<6.0

# Django REST Framework for APIs
djangorestframework>=3.14.0

# Environment configuration
python-decouple>=3.8

# Database adapter (PostgreSQL)
psycopg2-binary>=2.9.9

# Utilities
widget-tweaks>=1.5.0
EOF

echo -e "${GREEN}✓${NC} requirements.txt created"
echo ""

# Create installation script
echo -e "${BLUE}[5/7]${NC} Creating installation helper..."

cat > "$CORE_DIR/install.sh" << 'EOF'
#!/bin/bash
# Quick installation script for core app

set -e

echo "Core App Installation"
echo "====================="
echo ""

if [ -z "$1" ]; then
    echo "Usage: bash install.sh /path/to/django/project"
    exit 1
fi

TARGET="$1"

if [ ! -f "$TARGET/manage.py" ]; then
    echo "Error: Not a Django project (manage.py not found)"
    exit 1
fi

echo "Installing core app to: $TARGET"
echo ""

# Copy core app
cp -r core/ "$TARGET/core/"
echo "✓ Core app copied"

# Instructions
echo ""
echo "Next steps:"
echo ""
echo "1. Add 'core' to INSTALLED_APPS in settings.py"
echo "2. Run: python manage.py makemigrations core"
echo "3. Run: python manage.py migrate core"
echo "4. Run: python manage.py check"
echo ""
echo "Installation complete!"
EOF

chmod +x "$CORE_DIR/install.sh"
echo -e "${GREEN}✓${NC} Installation helper created"
echo ""

# Create package manifest
echo -e "${BLUE}[6/7]${NC} Creating package manifest..."

cat > "$CORE_DIR/MANIFEST.txt" << EOF
Core App Package Manifest
=========================

Package: $PACKAGE_NAME
Generated: $(date +"%Y-%m-%d %H:%M:%S")
Version: 1.0.0

Contents:
---------
EOF

cd "$CORE_DIR"
find . -type f -exec echo "  {}" \; | sort >> MANIFEST.txt

FILE_COUNT=$(find . -type f | wc -l)
TOTAL_SIZE=$(du -sh . | cut -f1)

cat >> MANIFEST.txt << EOF

Statistics:
-----------
Total files: $FILE_COUNT
Package size: $TOTAL_SIZE
Models: $MODEL_COUNT
Code lines: $MODEL_LINES

Checksums:
----------
EOF

# Add checksums for critical files
if command -v md5sum &> /dev/null; then
    md5sum core/models.py >> MANIFEST.txt 2>/dev/null || true
fi

cd - > /dev/null

echo -e "${GREEN}✓${NC} Package manifest created"
echo ""

# Create the tarball
echo -e "${BLUE}[7/7]${NC} Creating package archive..."

cd "$PACKAGE_DIR"
tar -czf "${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
cd - > /dev/null

ARCHIVE_SIZE=$(du -h "${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz" | cut -f1)

echo -e "${GREEN}✓${NC} Archive created: ${PACKAGE_NAME}.tar.gz ($ARCHIVE_SIZE)"
echo ""

# Cleanup
rm -rf "$PACKAGE_DIR"

# Summary
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}║         ✓ CORE APP PACKAGE CREATED                    ║${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Package Information:${NC}"
echo "  Name: ${PACKAGE_NAME}.tar.gz"
echo "  Location: ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
echo "  Size: $ARCHIVE_SIZE"
echo "  Models: $MODEL_COUNT"
echo "  Code lines: $MODEL_LINES"
echo "  Files: $FILE_COUNT"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo ""
echo "  Extract:"
echo "    tar -xzf ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
echo ""
echo "  Quick install:"
echo "    cd ${PACKAGE_NAME}"
echo "    bash install.sh /path/to/django/project"
echo ""
echo "  Automated migration:"
echo "    cd ${PACKAGE_NAME}"
echo "    bash scripts/migrate_core_app.sh /path/to/target/repo"
echo ""
echo -e "${GREEN}Package ready for deployment!${NC}"
echo ""

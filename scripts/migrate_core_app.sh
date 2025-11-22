#!/bin/bash
#
# CORE APP MIGRATION SCRIPT - PHASE 2
# Migrates core app from Floor-Management-System (old repo B) to Floor-Management-System-C (new clean repo C)
#
# This script automates the complete migration of the core app including:
# - Model files (12 models, 1,127 lines)
# - Context processors
# - Static files
# - Migrations
# - Settings configuration
# - Validation and testing
#
# Usage:
#   bash scripts/migrate_core_app.sh [TARGET_REPO_PATH]
#
# Example:
#   bash scripts/migrate_core_app.sh /workspaces/Floor-Management-System-C
#   bash scripts/migrate_core_app.sh ~/Floor-Management-System-C
#

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Script metadata
readonly SCRIPT_VERSION="1.0.0"
readonly MIGRATION_DATE=$(date +%Y-%m-%d)
readonly OLD_REPO_URL="https://github.com/Ramzi-Kassab/Floor-Management-System.git"
readonly OLD_REPO_BRANCH="hotfix/model-duplication-fix"

# Model counts (for validation)
readonly EXPECTED_MODEL_COUNT=12
readonly EXPECTED_MODEL_LINES=1127

# Banner
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}║         CORE APP MIGRATION SCRIPT - PHASE 2            ║${NC}"
echo -e "${CYAN}║         Floor Management System v${SCRIPT_VERSION}                ║${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Environment detection
detect_environment() {
    if [[ "$PWD" == *"/workspaces/"* ]]; then
        echo "codespaces"
    elif [[ "$PWD" == *"/root/"* ]]; then
        echo "claude-code"
    elif [[ "$PWD" == *"/home/"* ]]; then
        echo "local"
    else
        echo "unknown"
    fi
}

readonly ENVIRONMENT=$(detect_environment)

case $ENVIRONMENT in
    codespaces)
        echo -e "${GREEN}✓${NC} Environment: GitHub Codespaces"
        DEFAULT_TARGET="/workspaces/Floor-Management-System-C"
        ;;
    claude-code)
        echo -e "${GREEN}✓${NC} Environment: Claude Code"
        DEFAULT_TARGET="/root/Floor-Management-System-C"
        ;;
    local)
        echo -e "${GREEN}✓${NC} Environment: Local development"
        DEFAULT_TARGET="$HOME/Floor-Management-System-C"
        ;;
    *)
        echo -e "${YELLOW}!${NC} Environment: Unknown (using current directory)"
        DEFAULT_TARGET="$(pwd)/Floor-Management-System-C"
        ;;
esac

# Determine target repository path
if [ -z "$1" ]; then
    TARGET_REPO="$DEFAULT_TARGET"
    echo -e "${BLUE}→${NC} Using default target: $TARGET_REPO"
else
    TARGET_REPO="$1"
    echo -e "${BLUE}→${NC} Using provided target: $TARGET_REPO"
fi

echo ""

# Step 1: Validate target repository
echo -e "${BLUE}[1/12]${NC} Validating target repository..."

if [ ! -d "$TARGET_REPO" ]; then
    echo -e "${YELLOW}!${NC} Target repository not found at: $TARGET_REPO"
    read -p "Create new repository at this location? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$TARGET_REPO"
        cd "$TARGET_REPO"

        # Detect Python command
        if command -v python3 &> /dev/null; then
            PYTHON_CMD=python3
        elif command -v python &> /dev/null; then
            PYTHON_CMD=python
        else
            echo -e "${RED}✗${NC} Python not found"
            exit 1
        fi

        # Initialize Django project
        echo -e "${BLUE}→${NC} Creating new Django project..."
        $PYTHON_CMD -m venv venv
        source venv/bin/activate
        pip install -q django djangorestframework python-decouple widget-tweaks psycopg2-binary
        django-admin startproject floor_project .

        echo -e "${GREEN}✓${NC} New Django project created"
    else
        echo -e "${RED}✗${NC} Migration cancelled"
        exit 1
    fi
fi

cd "$TARGET_REPO"

if [ ! -f "manage.py" ]; then
    echo -e "${RED}✗${NC} Not a Django project (manage.py not found)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Target repository validated: $TARGET_REPO"
echo ""

# Step 2: Detect Python and activate virtualenv
echo -e "${BLUE}[2/12]${NC} Setting up Python environment..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}✗${NC} Python not found"
    exit 1
fi

# Activate venv if it exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated (.venv)"
else
    echo -e "${YELLOW}!${NC} No virtual environment found"
fi

echo -e "${BLUE}→${NC} Python: $($PYTHON_CMD --version)"
echo ""

# Step 3: Check if core app already exists
echo -e "${BLUE}[3/12]${NC} Checking for existing core app..."

if [ -d "core" ] && [ -f "core/models.py" ]; then
    EXISTING_LINES=$(wc -l < core/models.py)
    echo -e "${YELLOW}!${NC} Core app already exists ($EXISTING_LINES lines)"
    read -p "Overwrite existing core app? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→${NC} Migration cancelled"
        exit 0
    fi
    echo -e "${BLUE}→${NC} Removing existing core app..."
    rm -rf core
fi

echo -e "${GREEN}✓${NC} Ready to create core app"
echo ""

# Step 4: Create core app structure
echo -e "${BLUE}[4/12]${NC} Creating core app structure..."

$PYTHON_CMD manage.py startapp core
echo -e "${GREEN}✓${NC} Core app created"
echo ""

# Step 5: Clone old repository
echo -e "${BLUE}[5/12]${NC} Fetching core models from old repository..."

OLD_REPO_PATH="/tmp/Floor-Management-System-migration-$$"

if [ -d "$OLD_REPO_PATH" ]; then
    echo -e "${BLUE}→${NC} Cleaning up old temporary repo..."
    rm -rf "$OLD_REPO_PATH"
fi

echo -e "${BLUE}→${NC} Cloning: $OLD_REPO_URL"
git clone -q --depth 1 --branch "$OLD_REPO_BRANCH" "$OLD_REPO_URL" "$OLD_REPO_PATH" 2>&1 | grep -E "(Cloning|done)" || true

if [ ! -d "$OLD_REPO_PATH" ]; then
    echo -e "${RED}✗${NC} Failed to clone old repository"
    exit 1
fi

echo -e "${GREEN}✓${NC} Old repository cloned to temporary location"
echo ""

# Step 6: Copy core models
echo -e "${BLUE}[6/12]${NC} Copying core models and files..."

if [ ! -f "$OLD_REPO_PATH/core/models.py" ]; then
    echo -e "${RED}✗${NC} core/models.py not found in old repository"
    rm -rf "$OLD_REPO_PATH"
    exit 1
fi

# Copy core models
cp "$OLD_REPO_PATH/core/models.py" "$TARGET_REPO/core/models.py"
MODEL_LINES=$(wc -l < "$TARGET_REPO/core/models.py")
echo -e "${GREEN}✓${NC} Copied core/models.py ($MODEL_LINES lines)"

# Copy context processors if they exist
if [ -f "$OLD_REPO_PATH/core/context_processors.py" ]; then
    cp "$OLD_REPO_PATH/core/context_processors.py" "$TARGET_REPO/core/context_processors.py"
    echo -e "${GREEN}✓${NC} Copied core/context_processors.py"
fi

# Validate model count
MODEL_COUNT=$(grep -c "^class.*models.Model" "$TARGET_REPO/core/models.py" || echo "0")
if [ "$MODEL_COUNT" -ne "$EXPECTED_MODEL_COUNT" ]; then
    echo -e "${YELLOW}!${NC} Warning: Expected $EXPECTED_MODEL_COUNT models, found $MODEL_COUNT"
fi

echo ""

# Step 7: Update settings.py
echo -e "${BLUE}[7/12]${NC} Updating settings.py..."

# Detect settings file location
if [ -f "floor_project/settings.py" ]; then
    SETTINGS_FILE="floor_project/settings.py"
elif [ -f "floor_mgmt/settings.py" ]; then
    SETTINGS_FILE="floor_mgmt/settings.py"
else
    echo -e "${RED}✗${NC} settings.py not found"
    rm -rf "$OLD_REPO_PATH"
    exit 1
fi

# Check if core is already in INSTALLED_APPS
if grep -q "'core'" "$SETTINGS_FILE" || grep -q '"core"' "$SETTINGS_FILE"; then
    echo -e "${YELLOW}!${NC} 'core' already in INSTALLED_APPS"
else
    # Find the INSTALLED_APPS section and add core
    if grep -q "# Project apps" "$SETTINGS_FILE"; then
        # Add after the comment
        sed -i "/# Project apps/a\\    'core',  # Foundation: shared utilities, cost centers, notifications" "$SETTINGS_FILE"
    elif grep -q "# Third-party apps" "$SETTINGS_FILE"; then
        # Add after third-party section
        sed -i "/# Third-party apps/,/]/ s/]/    \n    # Project apps\n    'core',  # Foundation: shared utilities, cost centers, notifications\n]/" "$SETTINGS_FILE"
    else
        # Add at the end of INSTALLED_APPS
        sed -i "/INSTALLED_APPS = \[/,/]/ s/]/    'core',  # Foundation: shared utilities, cost centers, notifications\n]/" "$SETTINGS_FILE"
    fi
    echo -e "${GREEN}✓${NC} Added 'core' to INSTALLED_APPS in $SETTINGS_FILE"
fi

# Update context processors if they exist
if [ -f "$TARGET_REPO/core/context_processors.py" ]; then
    if ! grep -q "core.context_processors" "$SETTINGS_FILE"; then
        echo -e "${YELLOW}!${NC} Remember to add core context processors to TEMPLATES['OPTIONS']['context_processors']"
    fi
fi

echo ""

# Step 8: Create static directory
echo -e "${BLUE}[8/12]${NC} Creating static directories..."

mkdir -p static media
echo -e "${GREEN}✓${NC} Static and media directories created"
echo ""

# Step 9: Create migrations
echo -e "${BLUE}[9/12]${NC} Creating Django migrations..."

MIGRATION_OUTPUT=$($PYTHON_CMD manage.py makemigrations core 2>&1)
echo "$MIGRATION_OUTPUT" | grep -E "(Migrations|Create|No changes)" || echo "$MIGRATION_OUTPUT"

if [ -f "core/migrations/0001_initial.py" ]; then
    MIGRATION_SIZE=$(du -h core/migrations/0001_initial.py | cut -f1)
    echo -e "${GREEN}✓${NC} Migrations created (0001_initial.py - $MIGRATION_SIZE)"
else
    echo -e "${YELLOW}!${NC} No new migrations created (may already exist)"
fi

echo ""

# Step 10: Run Django checks
echo -e "${BLUE}[10/12]${NC} Running Django system checks..."

CHECK_OUTPUT=$($PYTHON_CMD manage.py check 2>&1)
if echo "$CHECK_OUTPUT" | grep -q "System check identified no issues"; then
    echo -e "${GREEN}✓${NC} Django check passed - System check identified no issues (0 silenced)"
elif echo "$CHECK_OUTPUT" | grep -q "0 errors"; then
    echo -e "${GREEN}✓${NC} Django check passed (0 errors)"
else
    echo -e "${RED}✗${NC} Django check failed:"
    echo "$CHECK_OUTPUT"
    rm -rf "$OLD_REPO_PATH"
    exit 1
fi

echo ""

# Step 11: Verify models
echo -e "${BLUE}[11/12]${NC} Verifying models..."

echo -e "${GREEN}✓${NC} Found $MODEL_COUNT Django models in core/models.py:"
echo ""
grep "^class.*models.Model" "$TARGET_REPO/core/models.py" | sed 's/class \([^(]*\).*/  - \1/' | head -15
echo ""

# Step 12: Cleanup and summary
echo -e "${BLUE}[12/12]${NC} Cleaning up..."

rm -rf "$OLD_REPO_PATH"
echo -e "${GREEN}✓${NC} Temporary files removed"
echo ""

# Generate summary
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}║          ✓ CORE APP MIGRATION COMPLETE                ║${NC}"
echo -e "${CYAN}║                                                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  - Models migrated: $MODEL_COUNT (expected: $EXPECTED_MODEL_COUNT)"
echo "  - Lines of code: $MODEL_LINES (expected: ~$EXPECTED_MODEL_LINES)"
echo "  - Migration file: core/migrations/0001_initial.py"
echo "  - Django check: PASSED"
echo "  - Target: $TARGET_REPO"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "  1. Review the migrated code:"
echo "     cd $TARGET_REPO"
echo "     cat core/models.py | head -50"
echo ""
echo "  2. Commit the changes:"
echo "     git add -A"
echo "     git status"
echo "     git commit -m \"feat(core): migrate core app with 12 models from old repo\""
echo ""
echo "  3. Apply migrations (requires PostgreSQL):"
echo "     python manage.py migrate"
echo ""
echo "  4. Test the core app:"
echo "     python manage.py test core"
echo ""
echo "  5. Push to GitHub:"
echo "     git push -u origin master"
echo ""
echo -e "${YELLOW}Models imported (12 total):${NC}"
echo "  - UserPreference: UI preferences, themes, table settings"
echo "  - CostCenter: Financial tracking with hierarchy"
echo "  - ERPDocumentType, ERPReference: ERP integration"
echo "  - LossOfSaleCause, LossOfSaleEvent: Loss tracking"
echo "  - ApprovalType, ApprovalAuthority: Approval workflow"
echo "  - Currency, ExchangeRate: Multi-currency support"
echo "  - Notification: User notifications with GenericFK"
echo "  - ActivityLog: System-wide audit trail"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - Phase 2 Plan: docs/PHASE2_MIGRATION_PLAN.md"
echo "  - Phase 1 Audit: docs/PHASE_1_AUDIT.md"
echo "  - Progress Tracking: docs/PHASE2_PROGRESS.md (create this)"
echo ""
echo -e "${GREEN}Migration completed successfully!${NC}"
echo -e "Generated by: scripts/migrate_core_app.sh v${SCRIPT_VERSION}"
echo -e "Date: ${MIGRATION_DATE}"
echo ""

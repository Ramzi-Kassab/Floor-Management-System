# Core App Migration Guide - Phase 2

**Document Version:** 1.0.0
**Last Updated:** 2025-11-22
**Status:** Ready for Production Use
**Part of:** Floor Management System Phase 2 Migration

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Methods](#migration-methods)
4. [Core App Architecture](#core-app-architecture)
5. [Step-by-Step Migration](#step-by-step-migration)
6. [Validation & Testing](#validation--testing)
7. [Troubleshooting](#troubleshooting)
8. [Post-Migration Tasks](#post-migration-tasks)
9. [Dependencies](#dependencies)
10. [API Reference](#api-reference)

---

## Overview

The **core app** is the foundational layer of the Floor Management System, providing shared utilities, data models, and services used throughout the application.

### Key Statistics

- **Models:** 12
- **Code Lines:** ~1,127
- **Migration Complexity:** Low (no circular dependencies)
- **Priority:** P0 (Foundation - must be first)
- **Estimated Time:** 1-2 hours

### What This App Provides

The core app contains models and utilities for:

1. **User Preferences** - UI customization, themes, table settings
2. **Cost Centers** - Financial tracking and budgeting
3. **ERP Integration** - Generic document reference system
4. **Loss Tracking** - Loss of sale cause and event tracking
5. **Approval Workflows** - Multi-level approval routing
6. **Multi-Currency** - Currency and exchange rate management
7. **Notifications** - System-wide user notification framework
8. **Audit Trail** - Activity logging for all models

### Why Core App First?

The core app **must** be migrated first because:

- ✅ **Zero dependencies** on other project apps
- ✅ **Foundation models** used by 8+ other apps
- ✅ **Generic foreign keys** allow flexible relationships
- ✅ **Well-designed** with no technical debt identified in Phase 1 audit
- ✅ **Clean migration** possible without modifications

---

## Prerequisites

### Required Software

```bash
# Python 3.10+
python --version  # or python3 --version

# Django 5.0+
pip show django

# PostgreSQL 13+ (recommended) or SQLite (development only)
psql --version

# Git
git --version
```

### Required Python Packages

```bash
pip install django>=5.0
pip install djangorestframework>=3.14.0
pip install python-decouple>=3.8
pip install psycopg2-binary>=2.9.9  # PostgreSQL
pip install widget-tweaks>=1.5.0
```

### Repository Access

- **Old Repository (Source):**
  https://github.com/Ramzi-Kassab/Floor-Management-System

- **Branch:** `hotfix/model-duplication-fix`

- **New Repository (Target):**
  Your clean Floor-Management-System-C repository

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify Django installation
python -c "import django; print(django.VERSION)"
```

---

## Migration Methods

### Method 1: Automated Script (Recommended)

**Best for:** Quick migration, Codespaces, first-time users

```bash
# Clone old repository
git clone https://github.com/Ramzi-Kassab/Floor-Management-System.git
cd Floor-Management-System
git checkout hotfix/model-duplication-fix

# Run migration script
bash scripts/migrate_core_app.sh /path/to/new/repo

# Follow prompts
```

**Pros:**
- ✅ Fully automated
- ✅ Built-in validation
- ✅ Rollback on errors
- ✅ Generates complete package

**Cons:**
- ❌ Less control over customization

### Method 2: Export Package

**Best for:** Offline migration, multiple deployments, archival

```bash
# In old repository
bash scripts/export_core_package.sh /tmp

# Extract package
cd /tmp
tar -xzf core_app_package_YYYYMMDD_HHMMSS.tar.gz
cd core_app_package_YYYYMMDD_HHMMSS

# Install to target
bash install.sh /path/to/new/repo

# Or use included migration script
bash scripts/migrate_core_app.sh /path/to/new/repo
```

**Pros:**
- ✅ Portable archive
- ✅ No git required
- ✅ Can be version-controlled separately
- ✅ Includes documentation

**Cons:**
- ❌ Extra step to create package

### Method 3: Manual Migration

**Best for:** Learning, customization, troubleshooting

See [Step-by-Step Migration](#step-by-step-migration) below.

**Pros:**
- ✅ Full control
- ✅ Educational
- ✅ Easy to customize

**Cons:**
- ❌ More time-consuming
- ❌ Potential for errors

---

## Core App Architecture

### Model Hierarchy

```
core/
├── UserPreference (1:1 with User)
│   └── Stores per-user UI preferences
│
├── CostCenter (Tree structure)
│   ├── parent → CostCenter (recursive)
│   └── Used by: JobCard, Department, MaintenanceRequest
│
├── ERP Integration
│   ├── ERPDocumentType (lookup table)
│   └── ERPReference (GenericFK)
│       └── Can link to any model
│
├── Loss Tracking
│   ├── LossOfSaleCause (lookup table)
│   └── LossOfSaleEvent (GenericFK)
│       └── Links to JobCard, Asset, etc.
│
├── Approval System
│   ├── ApprovalType (lookup table)
│   └── ApprovalAuthority (routing config)
│       └── Used by: Production, Purchasing, Finance
│
├── Multi-Currency
│   ├── Currency (master data)
│   └── ExchangeRate (historical rates)
│       └── Used by: Finance, Purchasing
│
└── System Services
    ├── Notification (GenericFK)
    │   └── User notifications for any object
    └── ActivityLog (GenericFK)
        └── Audit trail for any model
```

### Database Tables

| Table Name | Rows (typical) | Indexes | Foreign Keys |
|------------|----------------|---------|--------------|
| `core_user_preference` | 1 per user | User ID (PK) | User |
| `core_cost_center` | 50-200 | Code, Parent | Parent (self) |
| `core_erp_document_type` | 10-30 | Code | None |
| `core_erp_reference` | 1000s | Content Type, Object ID | ContentType |
| `core_loss_of_sale_cause` | 10-20 | Code | None |
| `core_loss_of_sale_event` | 100s | Content Type, Date | ContentType |
| `core_approval_type` | 5-15 | Code | None |
| `core_approval_authority` | 20-50 | Type, Min/Max Amount | ApprovalType |
| `core_currency` | 5-20 | Code | None |
| `core_exchange_rate` | 1000s | Currency, Date | Currency |
| `core_notification` | 1000s+ | User, Read status | User, ContentType |
| `core_activity_log` | 10000s+ | User, Date | User, ContentType |

### GenericForeignKey Usage

Four models use `GenericForeignKey` for maximum flexibility:

```python
# ERPReference - Can link to any model
erp_ref = ERPReference.objects.create(
    erp_document_type=doc_type,
    erp_document_number="SAP-12345",
    content_object=job_card  # Any model instance
)

# LossOfSaleEvent - Track losses for any object
loss = LossOfSaleEvent.objects.create(
    cause=cause,
    content_object=job_card,  # or asset, or quote
    estimated_loss_amount=50000
)

# Notification - Notify about any object
notif = Notification.objects.create(
    user=user,
    title="Job Card Updated",
    content_object=job_card,  # Link to related object
    priority="high"
)

# ActivityLog - Audit any model change
log = ActivityLog.objects.create(
    user=user,
    action="update",
    content_object=job_card,  # Object being changed
    changes={"status": ["pending", "approved"]}
)
```

**Important:** GenericForeignKey requires `django.contrib.contenttypes` in `INSTALLED_APPS`.

---

## Step-by-Step Migration

### Step 1: Prepare Target Repository

```bash
# Create or navigate to target repository
cd /path/to/Floor-Management-System-C

# Ensure it's a Django project
ls -l manage.py  # Should exist

# Activate virtual environment
source venv/bin/activate

# Verify Django
python manage.py --version
```

### Step 2: Create Core App Structure

```bash
# Create core app
python manage.py startapp core

# Verify structure
ls -R core/
# Expected:
# core/
#   __init__.py
#   admin.py
#   apps.py
#   models.py (empty/default)
#   tests.py
#   views.py
#   migrations/
#     __init__.py
```

### Step 3: Copy Core Models

```bash
# Clone old repository temporarily
cd /tmp
git clone https://github.com/Ramzi-Kassab/Floor-Management-System.git
cd Floor-Management-System
git checkout hotfix/model-duplication-fix

# Copy core models
cp core/models.py /path/to/Floor-Management-System-C/core/models.py

# Optional: Copy context processors if they exist
if [ -f core/context_processors.py ]; then
    cp core/context_processors.py /path/to/Floor-Management-System-C/core/context_processors.py
fi

# Return to target repo
cd /path/to/Floor-Management-System-C
```

### Step 4: Update Settings

Edit your `settings.py` (likely in `floor_project/settings.py` or similar):

```python
# In INSTALLED_APPS, add core:

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # Required for GenericFK!
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'widget_tweaks',

    # Project apps
    'core',  # ← Add this
]
```

**If you copied context_processors.py**, also add:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_preferences',  # ← Add these
                'core.context_processors.global_settings',   # ← if present
            ],
        },
    },
]
```

### Step 5: Create Migrations

```bash
# Create initial migration
python manage.py makemigrations core

# Expected output:
# Migrations for 'core':
#   core/migrations/0001_initial.py
#     - Create model UserPreference
#     - Create model CostCenter
#     - Create model ERPDocumentType
#     - Create model ERPReference
#     - Create model LossOfSaleCause
#     - Create model LossOfSaleEvent
#     - Create model ApprovalType
#     - Create model ApprovalAuthority
#     - Create model Currency
#     - Create model ExchangeRate
#     - Create model Notification
#     - Create model ActivityLog
#     - Add index core_user_preference_user_id_idx
#     - Add index core_cost_center_code_idx
#     - ... (additional indexes)

# Check migration file size (should be ~40-45KB)
du -h core/migrations/0001_initial.py
```

### Step 6: Run System Checks

```bash
# Run Django checks
python manage.py check

# Expected output:
# System check identified no issues (0 silenced).

# Or:
# System check identified no issues.
```

**Common issues and fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'django'` | Virtual env not activated | `source venv/bin/activate` |
| `ContentType matching query does not exist` | Missing contenttypes app | Add to INSTALLED_APPS |
| `No such table: django_content_type` | Migrations not run | `python manage.py migrate` |

### Step 7: Apply Migrations

**Important:** This requires a configured database.

```bash
# For PostgreSQL (recommended)
# Ensure .env or settings.py has:
#   DB_NAME=floor_management_c
#   DB_USER=postgres
#   DB_PASSWORD=yourpassword
#   DB_HOST=localhost
#   DB_PORT=5432

# Run migrations
python manage.py migrate core

# Expected output:
# Running migrations:
#   Applying core.0001_initial... OK

# Verify tables created
python manage.py dbshell
# In psql:
\dt core_*
# Should show 12 tables

# Exit:
\q
```

### Step 8: Verify Models

```bash
# Test model import
python manage.py shell

# In shell:
>>> from core.models import UserPreference, CostCenter, Notification
>>> print("✓ Models imported successfully")
>>>
>>> # Count models
>>> from django.apps import apps
>>> core_models = apps.get_app_config('core').get_models()
>>> print(f"Core app has {len(core_models)} models")
>>> # Should output: Core app has 12 models
>>>
>>> exit()
```

### Step 9: Create Initial Data (Optional)

```bash
# Create a fixture or use Django shell
python manage.py shell

# Example: Create default currency
>>> from core.models import Currency
>>> usd = Currency.objects.create(
...     code='USD',
...     name='US Dollar',
...     symbol='$',
...     is_active=True
... )
>>> print(f"✓ Created {usd}")
```

### Step 10: Commit Changes

```bash
# Stage all changes
git add -A

# Check status
git status
# Should show:
#   new file:   core/__init__.py
#   new file:   core/admin.py
#   new file:   core/apps.py
#   new file:   core/models.py
#   new file:   core/migrations/0001_initial.py
#   new file:   core/migrations/__init__.py
#   new file:   core/tests.py
#   new file:   core/views.py
#   modified:   floor_project/settings.py

# Create commit
git commit -m "feat(core): migrate core app with 12 models from old repo

Migrated complete core app from Floor-Management-System (old repo B):

Models Imported (12 total):
- UserPreference: UI preferences, themes, table settings
- CostCenter: Financial tracking with hierarchy
- ERPDocumentType, ERPReference: ERP integration
- LossOfSaleCause, LossOfSaleEvent: Loss tracking
- ApprovalType, ApprovalAuthority: Approval workflow
- Currency, ExchangeRate: Multi-currency support
- Notification: User notifications with GenericFK
- ActivityLog: System-wide audit trail

Implementation:
✅ All models with proper db_table settings
✅ GenericForeignKey relationships preserved
✅ All Meta configurations (indexes, constraints)
✅ Migrations created successfully
✅ Django check passes with 0 errors

Phase 2 Migration - Core app complete."

# Push to GitHub
git push origin master
```

---

## Validation & Testing

### Quick Validation Checklist

```bash
# ✓ Django check passes
python manage.py check
# Expected: System check identified no issues

# ✓ Migrations created
ls -lh core/migrations/0001_initial.py
# Expected: ~40-45KB file

# ✓ Models count correct
python -c "from django.apps import apps; print(len(apps.get_app_config('core').get_models()))"
# Expected: 12

# ✓ No import errors
python -c "from core.models import UserPreference, CostCenter, Notification, ActivityLog; print('OK')"
# Expected: OK

# ✓ Database tables exist (after migrate)
python manage.py dbshell -c "\dt core_*"
# Expected: List of 12 tables
```

### Unit Testing

Create `core/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import (
    UserPreference, CostCenter, Currency,
    Notification, ActivityLog
)

User = get_user_model()

class CoreModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_user_preference_creation(self):
        """Test UserPreference model"""
        pref = UserPreference.objects.create(
            user=self.user,
            theme='dark',
            sidebar_collapsed=True
        )
        self.assertEqual(pref.theme, 'dark')
        self.assertTrue(pref.sidebar_collapsed)

    def test_cost_center_hierarchy(self):
        """Test CostCenter parent-child relationship"""
        parent = CostCenter.objects.create(
            code='CC-001',
            name='Engineering',
            is_active=True
        )
        child = CostCenter.objects.create(
            code='CC-001-01',
            name='Design',
            parent=parent,
            is_active=True
        )
        self.assertEqual(child.parent, parent)

    def test_currency_creation(self):
        """Test Currency model"""
        usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_active=True
        )
        self.assertEqual(str(usd), 'USD - US Dollar')

    def test_notification_generic_fk(self):
        """Test Notification with GenericForeignKey"""
        cost_center = CostCenter.objects.create(
            code='CC-TEST',
            name='Test Center'
        )
        notif = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            content_object=cost_center,
            priority='medium'
        )
        self.assertEqual(notif.content_object, cost_center)
        self.assertFalse(notif.is_read)
```

Run tests:

```bash
# Run all core tests
python manage.py test core

# Run with verbosity
python manage.py test core --verbosity=2

# Run specific test
python manage.py test core.tests.CoreModelsTestCase.test_user_preference_creation
```

### Integration Testing

Test core models with Django admin:

```bash
# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Open browser: http://localhost:8000/admin/
# Login and verify you can see:
# - User preferences
# - Cost centers
# - Currencies
# - Notifications
# etc.
```

---

## Troubleshooting

### Issue: Django check fails with "core not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'core'
```

**Solution:**
```bash
# Verify core app exists
ls -R core/

# Verify core in INSTALLED_APPS
grep -n "core" settings.py

# Try importing directly
python -c "import core"
```

### Issue: Migrations not created

**Symptom:**
```
No changes detected in app 'core'
```

**Solution:**
```bash
# Ensure models.py has content
wc -l core/models.py
# Should show ~1,127 lines

# Try explicit migration
python manage.py makemigrations core --verbosity=2

# Check if migrations already exist
ls core/migrations/
```

### Issue: GenericForeignKey errors

**Symptom:**
```
FieldError: Cannot resolve keyword 'content_type' into field
```

**Solution:**
```python
# Ensure django.contrib.contenttypes is in INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # ← Must be present
    # ...
    'core',
]

# Run migrations for contenttypes
python manage.py migrate contenttypes
```

### Issue: Database table names don't match

**Symptom:**
```
ProgrammingError: relation "core_userpreference" does not exist
```

**Solution:**
```bash
# Check if migrations were applied
python manage.py showmigrations core

# If not applied:
python manage.py migrate core

# If already applied but table missing, check db_table in models:
grep -n "db_table" core/models.py
```

### Issue: Context processor errors

**Symptom:**
```
ImproperlyConfigured: context processor 'core.context_processors.user_preferences' not found
```

**Solution:**
```bash
# Check if file exists
ls -l core/context_processors.py

# If not, remove from TEMPLATES in settings.py
# Or copy from old repo:
cp /path/to/old/repo/core/context_processors.py core/
```

---

## Post-Migration Tasks

### 1. Configure Django Admin

Create `core/admin.py`:

```python
from django.contrib import admin
from core.models import (
    UserPreference, CostCenter, ERPDocumentType, ERPReference,
    LossOfSaleCause, LossOfSaleEvent, ApprovalType, ApprovalAuthority,
    Currency, ExchangeRate, Notification, ActivityLog
)

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'sidebar_collapsed']
    search_fields = ['user__username']

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'priority', 'is_read', 'created_at']
    list_filter = ['priority', 'is_read', 'created_at']
    search_fields = ['user__username', 'title']

# Add other models as needed
```

### 2. Create Initial Fixtures

```bash
# Export reference data for reuse
python manage.py dumpdata core.Currency --indent=2 > fixtures/currencies.json
python manage.py dumpdata core.ERPDocumentType --indent=2 > fixtures/erp_document_types.json
python manage.py dumpdata core.ApprovalType --indent=2 > fixtures/approval_types.json

# Load fixtures in new environments
python manage.py loaddata fixtures/currencies.json
```

### 3. Update Documentation

Create `core/README.md`:

```markdown
# Core App

Foundation app for Floor Management System.

## Models

- **UserPreference**: User UI customization
- **CostCenter**: Financial tracking and budgeting
- **ERPReference**: ERP integration (GenericFK)
- **LossOfSaleEvent**: Loss tracking (GenericFK)
- **ApprovalAuthority**: Approval routing
- **Currency/ExchangeRate**: Multi-currency support
- **Notification**: User notifications (GenericFK)
- **ActivityLog**: Audit trail (GenericFK)

## Usage

See: docs/CORE_APP_MIGRATION_GUIDE.md
```

### 4. Proceed to Next App

According to Phase 2 plan, next apps to migrate:

1. **hr** (P1) - 28 models, 3-4 days effort
2. **inventory** (P1) - 18 models, 3-4 days effort
3. **engineering** (P2) - 11 models, 2-3 days effort

Dependency order:
- HR and Inventory can be done in parallel (both depend only on core)
- Engineering depends on inventory (BitDesign, BillOfMaterials)

---

## Dependencies

### Core App Depends On

**Django built-in apps:**
- `django.contrib.auth` - User model
- `django.contrib.contenttypes` - GenericForeignKey support

**Third-party apps:**
- None (core has zero third-party dependencies!)

### Apps That Depend On Core

| App | Uses These Core Models |
|-----|------------------------|
| **hr** | CostCenter, Notification, ActivityLog |
| **inventory** | CostCenter, ERPReference, Notification |
| **production** | CostCenter, ApprovalAuthority, LossOfSaleEvent |
| **finance** | CostCenter, Currency, ExchangeRate, ApprovalAuthority |
| **purchasing** | Currency, ExchangeRate, ApprovalAuthority |
| **maintenance** | CostCenter, Notification, ActivityLog |
| **quality** | Notification, ActivityLog |
| **analytics** | ActivityLog |

**Migration order rule:** Core must be migrated before any dependent app.

---

## API Reference

### Model Methods

```python
# UserPreference
user_pref = UserPreference.objects.get(user=request.user)
theme = user_pref.theme  # 'light', 'dark', 'auto'

# CostCenter
cc = CostCenter.objects.get(code='CC-001')
children = cc.children.all()  # Related name for child cost centers
is_within_budget = cc.is_within_budget()  # Check budget status

# Currency
usd = Currency.objects.get(code='USD')
rate = usd.get_exchange_rate(to_currency='SAR', date=today)

# Notification
notif = Notification.objects.create(
    user=user,
    title="Job Card #123 Approved",
    content_object=job_card,  # Any model instance
    priority="high"
)
notif.mark_as_read()

# ActivityLog
ActivityLog.log_action(
    user=request.user,
    action="update",
    content_object=job_card,
    changes={"status": ["pending", "approved"]}
)
```

### Querying GenericForeignKey

```python
from django.contrib.contenttypes.models import ContentType

# Find all notifications for a specific object
job_card_ct = ContentType.objects.get_for_model(JobCard)
notifications = Notification.objects.filter(
    content_type=job_card_ct,
    object_id=job_card.id
)

# Find all activity logs for user in last 7 days
logs = ActivityLog.objects.filter(
    user=user,
    created_at__gte=now() - timedelta(days=7)
)

# Find ERP references for any object
erp_refs = ERPReference.objects.filter(
    content_type=job_card_ct,
    object_id=job_card.id
)
```

---

## Summary

### Checklist

- [ ] Prerequisites met (Python, Django, database)
- [ ] Virtual environment activated
- [ ] Core app created
- [ ] Models copied from old repo
- [ ] Settings updated (INSTALLED_APPS)
- [ ] Migrations created
- [ ] Django check passes (0 errors)
- [ ] Migrations applied
- [ ] Models verified (12 total)
- [ ] Tests created and passing
- [ ] Admin configured
- [ ] Changes committed to git
- [ ] Pushed to GitHub
- [ ] Ready for next app migration

### Time Estimate

- **Automated method:** 10-20 minutes
- **Manual method:** 1-2 hours
- **With testing:** 2-3 hours

### Support

For issues or questions:
1. See [Troubleshooting](#troubleshooting) section
2. Review `docs/PHASE2_MIGRATION_PLAN.md`
3. Check `docs/PHASE_1_AUDIT.md` for context
4. Use automated scripts in `scripts/` directory

---

**Document maintained by:** Floor Management System Migration Team
**Last reviewed:** 2025-11-22
**Next review:** After first 3 app migrations complete

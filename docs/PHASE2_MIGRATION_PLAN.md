# PHASE 2: MIGRATION PLAN TO PROJECT C

**Date:** 2025-11-22
**Status:** Planning - Ready for Execution
**Target:** `floor_management_system-C` (New Clean Repository)
**Source:** `Floor-Management-System` (Old Repository - Read Only)

---

## EXECUTIVE SUMMARY

This migration plan details the systematic approach to build a clean Floor Management System (C) using the old system (B) as a reference. Based on the comprehensive Phase 1 audit, we will selectively migrate code, eliminating technical debt and consolidating duplicate systems.

**Migration Strategy:**
- ✅ **Selective Migration** - Not copying everything, only canonical implementations
- ✅ **App-by-App** - One Django app per branch, incremental progress
- ✅ **Unified Design** - Consolidate duplicate Evaluation/Production systems
- ✅ **Quality First** - Tests and documentation from day one

**Estimated Timeline:** 6-8 weeks
**Risk Level:** Low-Medium (controlled, incremental approach)

---

## TABLE OF CONTENTS

1. [Pre-Migration Setup](#1-pre-migration-setup)
2. [Foundation Apps Migration](#2-foundation-apps-migration)
3. [Supporting Apps Migration](#3-supporting-apps-migration)
4. [Unified Production & Evaluation](#4-unified-production--evaluation)
5. [Documentation Migration](#5-documentation-migration)
6. [Testing Infrastructure](#6-testing-infrastructure)
7. [Final Integration](#7-final-integration)
8. [Success Criteria](#8-success-criteria)

---

## 1. PRE-MIGRATION SETUP

### 1.1 Prerequisites Checklist

**Old Repo (B) - Read-Only Reference:**
- [ ] Branch `hotfix/model-duplication-fix` checked out (latest code)
- [ ] Branch `claude/refactoring-master-prompt-01TJVoXKxvTqDKEXq8DWk539` available (Phase 1 audit)
- [ ] Phase 1 audit document read and understood
- [ ] Template analysis reviewed (142 orphaned templates identified)
- [ ] Duplicate systems documented (Evaluation/Production overlap)

**New Repo (C) - Active Development:**
- [ ] Django 5.2.6 project created
- [ ] PostgreSQL database `floor_management_c` configured
- [ ] Virtual environment set up with dependencies
- [ ] `python manage.py check` passes (0 errors)
- [ ] `python manage.py runserver` works
- [ ] Git initialized with main branch
- [ ] GitHub remote repository created and connected
- [ ] Initial commit with Django skeleton

### 1.2 Development Environment

**Required Tools:**
```bash
# Python & Django
Python 3.11+
Django 5.2.6
djangorestframework
django-widget-tweaks
python-decouple

# Database
PostgreSQL 13+
psycopg2-binary

# Testing
pytest
pytest-django
coverage

# Development
black (code formatting)
flake8 (linting)
```

**Database Connection String:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'floor_management_c',
        'USER': '<your_user>',
        'PASSWORD': '<your_password>',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 1.3 Directory Structure for C

```
floor_management_system-C/
├── floor_mgmt/              # Project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                    # All Django apps (new structure)
│   ├── core/               # Foundation: shared utilities
│   ├── hr/                 # Foundation: human resources
│   ├── inventory/          # Foundation: items, stock, locations
│   ├── engineering/        # Foundation: bit design, BOM
│   ├── sales/              # Foundation: customers, orders
│   ├── evaluation/         # Core: NDT, thread, cutter evaluation
│   ├── production/         # Core: job cards, routing, checklists
│   ├── quality/            # Supporting: NCR, calibration
│   ├── qrcodes/            # Supporting: QR code system
│   ├── maintenance/        # Supporting: asset maintenance
│   ├── purchasing/         # Supporting: procurement
│   ├── planning/           # Supporting: planning, metrics
│   ├── knowledge/          # Supporting: knowledge base
│   └── analytics/          # Supporting: metrics, monitoring
├── templates/              # Project-wide base templates
│   └── base.html
├── static/                 # Project-wide static files
│   ├── css/
│   ├── js/
│   └── images/
├── media/                  # User uploads
├── docs/                   # Documentation
│   ├── PHASE1_AUDIT.md    # Copied from B
│   ├── PHASE2_MIGRATION_PLAN.md  # This document
│   ├── ARCHITECTURE.md
│   ├── TESTING.md
│   └── API_DOCUMENTATION.md
├── tests/                  # Project-wide tests
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

**Note:** Using `apps/` directory for cleaner organization vs flat structure in old repo.

---

## 2. FOUNDATION APPS MIGRATION

Foundation apps provide core functionality needed by all other apps. Migrate in dependency order.

### 2.1 App: CORE

**Branch:** `feature/core-from-B`

**Purpose:** System-wide shared utilities, cost centers, notifications, activity logs.

#### Models to Import (12 models from `core/models.py`):

| Model | DB Table | Purpose | Import? |
|-------|----------|---------|---------|
| UserPreference | core_user_preference | UI preferences, themes | ✅ Yes |
| CostCenter | core_cost_center | Financial tracking | ✅ Yes |
| ERPDocumentType | core_erp_document_type | ERP integration | ✅ Yes |
| ERPReference | core_erp_reference | ERP mapping | ✅ Yes |
| LossOfSaleCause | core_loss_of_sale_cause | Sales tracking | ✅ Yes |
| LossOfSaleEvent | core_loss_of_sale_event | Sales incidents | ✅ Yes |
| ApprovalType | core_approval_type | Approval workflow | ✅ Yes |
| ApprovalAuthority | core_approval_authority | Approval config | ✅ Yes |
| Currency | core_currency | Currency master | ✅ Yes |
| ExchangeRate | core_exchange_rate | FX rates | ✅ Yes |
| Notification | core_notification | User notifications | ✅ Yes |
| ActivityLog | core_activity_log | Audit trail | ✅ Yes |

#### Views to Import:

From `core/views.py`:
- ✅ Main dashboard view
- ✅ Finance dashboard view
- ✅ User preference views
- ✅ Global search functionality
- ✅ Health check endpoint

#### Templates to Import:

**From:** `core/templates/core/` (app-specific, canonical)
- ✅ main_dashboard.html
- ✅ finance_dashboard.html
- ✅ user_preferences.html
- ✅ search_results.html
- ✅ Cost center templates (list, detail, form)
- ✅ Loss of sale templates
- ✅ Partials: data_table.html, erp_badge.html

**Skip:** Nothing - all core templates are canonical

#### URLs to Import:

From `core/urls.py`:
- ✅ All URL patterns (approximately 42 URLs)
- ✅ Maintain namespace: `core:`

#### Additional Files:

- ✅ `core/context_processors.py` - User preferences, global settings
- ✅ `core/forms.py` - Core forms
- ✅ `core/export_utils.py` - Export functionality
- ✅ `core/search_utils.py` - Global search
- ✅ `core/notification_utils.py` - Notification helpers
- ✅ `core/health.py` - Health check utilities
- ✅ `core/templatetags/core_tags.py` - Template tags

#### Migration Steps:

1. Create app: `python manage.py startapp core` in `apps/core/`
2. Copy models from B → C, review and clean
3. Copy views, ensuring imports are correct
4. Copy templates to `apps/core/templates/core/`
5. Copy URLs with namespace
6. Copy utility modules
7. Add to `INSTALLED_APPS`: `'apps.core'`
8. Create migrations: `python manage.py makemigrations core`
9. Run migrations: `python manage.py migrate`
10. Test: Visit main dashboard, check health endpoint
11. Commit: `feat(core): initial import from B with cleanup`

#### Testing Plan:

```python
# apps/core/tests/test_models.py
def test_cost_center_creation()
def test_user_preference_defaults()
def test_currency_exchange_rate()

# apps/core/tests/test_views.py
def test_main_dashboard_loads()
def test_search_functionality()
def test_health_check_endpoint()
```

**Estimated Effort:** 1-2 days

---

### 2.2 App: HR (Human Resources)

**Branch:** `feature/hr-from-B`

**Purpose:** Employee management, departments, positions, leave, attendance, training, documents.

**Dependencies:** `core` (for CostCenter)

#### Models to Import (20+ models from `floor_app/operations/hr/models/`):

**Core HR Models:**
| Model | File | Import? |
|-------|------|---------|
| HRPeople | people.py | ✅ Yes - Canonical person record |
| HREmployee | employee.py | ✅ Yes - Employment details |
| Department | department.py | ✅ Yes - Org structure |
| Position | position.py | ✅ Yes - Job positions |
| HRPhone | phone.py | ✅ Yes - Personal phone numbers |
| HREmail | email.py | ✅ Yes - Email addresses |
| HRAuditLog | audit_log.py | ✅ Yes - Audit trail |

**HRMS Features:**
| Feature | Models | Import? |
|---------|--------|---------|
| Leave Management | LeavePolicy, LeaveBalance, LeaveRequest, LeaveType, LeaveRequestStatus | ✅ Yes |
| Attendance | AttendanceRecord, OvertimeRequest, AttendanceSummary, etc. | ✅ Yes |
| Training | TrainingProgram, TrainingSession, EmployeeTraining, SkillMatrix | ✅ Yes |
| Documents | EmployeeDocument, DocumentRenewal, ExpiryAlert, DocumentType | ✅ Yes |
| Qualification | QualificationLevel, EmployeeQualification | ✅ Yes |
| Configuration | OvertimeConfiguration, AttendanceConfiguration, DelayIncident | ✅ Yes |

**Note:** HR app in B is very comprehensive (55 templates, 20+ models). This is good quality code.

#### Views to Import:

From `floor_app/operations/hr/`:
- ✅ `views_employee_wizard.py` (1,278 lines) - Employee setup wizard
- ✅ `views_employee_setup.py` (688 lines) - Employee management
- ✅ views for leave, attendance, training, documents
- ✅ Department and position CRUD
- ❌ **DO NOT import:** Legacy employee views from `floor_app/views.py` (deprecated)

#### Templates to Import:

**From:** `floor_app/operations/hr/templates/hr/` (app-specific, 55 templates)
- ✅ All employee templates (wizard, portal, detail, list)
- ✅ All leave templates
- ✅ All attendance templates
- ✅ All training templates
- ✅ All document templates
- ✅ Department and position templates

**Skip:** None - HR templates are canonical

#### URLs:

From `floor_app/operations/hr/urls.py`:
- ✅ All HR URL patterns (namespace: `hr:`)
- ✅ API endpoints from `floor_app/operations/hr/api/urls.py`

#### Additional Files:

- ✅ All model files from `models/` directory
- ✅ All test files (good examples: `tests/test_position_crud.py` - 677 lines)
- ✅ Forms, serializers, mixins

#### Migration Steps:

1. Create app: `apps/hr/`
2. Copy all models (organized in models/ directory)
3. Copy views (employee wizard, setup, CRUD)
4. Copy 55 templates
5. Copy URLs and API endpoints
6. Copy tests (important: HR has good test coverage)
7. Add to `INSTALLED_APPS`: `'apps.hr'`
8. Create migrations
9. Test: Employee creation wizard, leave requests, attendance
10. Commit

**Estimated Effort:** 3-4 days (large app, comprehensive features)

---

### 2.3 App: INVENTORY

**Branch:** `feature/inventory-from-B`

**Purpose:** Items, stock, locations, cutters, inventory transactions.

**Dependencies:** `core`

#### Models to Import (20+ models from `floor_app/operations/inventory/models/`):

**Reference Models** (`reference.py`):
| Model | Purpose | Import? |
|-------|---------|---------|
| ConditionType | NEW, USED, RECLAIM | ✅ Yes |
| OwnershipType | ARDT, ENO, CUSTOMER | ✅ Yes |
| UnitOfMeasure | PC, KG, L, M | ✅ Yes |
| ItemCategory | Hierarchical categories | ✅ Yes |

**Item Master** (`item.py`):
| Model | Purpose | Import? |
|-------|---------|---------|
| Item | Master inventory catalog | ✅ Yes |

**Stock Models** (`stock.py`):
| Model | Purpose | Import? |
|-------|---------|---------|
| Location | Storage locations | ✅ Yes |
| SerialUnit | Serial-tracked units | ✅ Yes |
| SerialUnitMATHistory | MAT change history | ✅ Yes |
| InventoryStock | Stock levels | ✅ Yes |

**Cutter Models** (`cutter.py`, `cutter_bom_grid.py`):
| Model | Purpose | Import? |
|-------|---------|---------|
| CutterOwnershipCategory | Ownership categories | ✅ Yes |
| CutterDetail | Cutter details | ✅ Yes |
| CutterPriceHistory | Price tracking | ✅ Yes |
| CutterInventorySummary | Summary views | ✅ Yes |
| CutterBOMGridHeader | BOM grid header | ✅ Yes |
| CutterBOMGridCell | BOM grid cells | ✅ Yes |
| CutterBOMSummary | BOM summaries | ✅ Yes |
| CutterMapHeader | Cutter mapping | ✅ Yes |
| CutterMapCell | Map cells | ✅ Yes |
| BOMUsageTracking | Usage tracking | ✅ Yes |

**Note:** Cutter BOM grid is complex (972-line model file). Important for workshop operations.

#### Views to Import:

From `floor_app/operations/inventory/views.py` (835 lines):
- ✅ Item CRUD views
- ✅ Stock management views
- ✅ Location management (including tree view)
- ✅ Serial unit tracking
- ✅ Cutter management
- ✅ BOM grid views

From `floor_app/operations/inventory/api/views.py` (787 lines):
- ✅ API endpoints for inventory operations

#### Templates to Import:

**From:** `floor_app/operations/inventory/templates/inventory/` (32 templates, canonical)
- ✅ Items: list, detail, form
- ✅ Serial units: list, detail, form
- ✅ Stock: list, detail, form
- ✅ Locations: list, detail, form, tree_node.html
- ✅ Cutters: all templates
- ✅ BOM grid templates
- ✅ Settings/dashboard

**Skip:** Centralized templates in `floor_app/templates/inventory/` (25 orphaned templates)

#### Migration Steps:

1. Create app: `apps/inventory/`
2. Copy reference models first (dependencies for other apps)
3. Copy item, stock, location models
4. Copy cutter and BOM grid models (complex, test thoroughly)
5. Copy views and API endpoints
6. Copy 32 canonical templates
7. Copy URLs
8. Add to `INSTALLED_APPS`
9. Create migrations
10. Test: Create items, locations, stock transactions
11. Commit

**Testing Priority:**
- Location tree structure
- Serial unit tracking
- Cutter BOM grid functionality
- Stock level calculations

**Estimated Effort:** 3-4 days (complex domain, critical for operations)

---

### 2.4 App: ENGINEERING

**Branch:** `feature/engineering-from-B`

**Purpose:** Bit design, BOM (Bill of Materials), roller cone designs.

**Dependencies:** `inventory` (for Item, ConditionType, OwnershipType, UnitOfMeasure)

#### Models to Import (11 models from `floor_app/operations/engineering/models/`):

**Bit Design Models** (`bit_design.py`):
| Model | DB Table | Notes |
|-------|----------|-------|
| BitDesignLevel | inventory_bit_design_level | ✅ Import - Preserve table name |
| BitDesignType | inventory_bit_design_type | ✅ Import - Preserve table name |
| BitDesign | inventory_bit_design | ✅ Import - Preserve table name |
| BitDesignRevision | inventory_bit_design_revision | ✅ Import - Preserve table name |

**BOM Models** (`bom.py`):
| Model | DB Table | Notes |
|-------|----------|-------|
| BOMHeader | inventory_bom_header | ✅ Import - Preserve table name |
| BOMLine | inventory_bom_line | ✅ Import - Preserve table name |

**Roller Cone Models** (`roller_cone.py`):
| Model | Purpose | Import? |
|-------|---------|---------|
| RollerConeBitType | Roller cone types | ✅ Yes |
| RollerConeBearing | Bearing types | ✅ Yes |
| RollerConeSeal | Seal types | ✅ Yes |
| RollerConeDesign | Design specs | ✅ Yes |
| RollerConeComponent | Components | ✅ Yes |
| RollerConeBOM | BOM for roller cone | ✅ Yes |

**Important:** These models were successfully refactored in the old repo from `inventory` to `engineering` while preserving database table names (to avoid data migration). Keep this design in C.

#### Views to Import:

Engineering app in B doesn't have views yet - bit design/BOM views are in inventory app.

**In C, create views in engineering app:**
- ✅ BitDesign CRUD (migrate from inventory views)
- ✅ BitDesignRevision management (MAT numbers)
- ✅ BOM header/line management
- ✅ Roller cone design views

#### Templates to Import:

**No templates in engineering app in B.** Bit design templates are in inventory app.

**In C, organize templates:**
- Create `apps/engineering/templates/engineering/`
- ✅ Move bit design templates from inventory to engineering
- ✅ Move BOM templates from inventory to engineering
- Structure:
  ```
  engineering/templates/engineering/
  ├── bit_designs/
  │   ├── list.html
  │   ├── detail.html
  │   ├── form.html
  │   ├── mat_list.html
  │   ├── mat_detail.html
  │   └── mat_form.html
  ├── boms/
  │   ├── list.html
  │   ├── detail.html
  │   └── form.html
  └── roller_cone/
      └── ... (create as needed)
  ```

#### URLs:

**In B:** Bit design/BOM URLs are in inventory app.

**In C:** Create engineering URLs:
```python
# apps/engineering/urls.py
app_name = 'engineering'
urlpatterns = [
    path('bit-designs/', views.bitdesign_list, name='bitdesign_list'),
    path('bit-designs/<int:pk>/', views.bitdesign_detail, name='bitdesign_detail'),
    path('mats/', views.mat_list, name='mat_list'),
    path('mats/<int:pk>/', views.mat_detail, name='mat_detail'),
    path('boms/', views.bom_list, name='bom_list'),
    path('boms/<int:pk>/', views.bom_detail, name='bom_detail'),
    # ... roller cone URLs
]
```

#### Migration Steps:

1. Create app: `apps/engineering/`
2. Copy models (preserve db_table names)
3. **Extract** bit design/BOM views from inventory app in B
4. Create engineering views in C
5. **Extract** bit design/BOM templates from inventory app in B
6. Create engineering templates in C
7. Create engineering URLs
8. Update inventory app in C to remove bit design/BOM (moved to engineering)
9. Add to `INSTALLED_APPS`: `'apps.engineering'`
10. Create migrations with preserved table names
11. Test: Bit design CRUD, BOM management
12. Commit

**Important:** This completes the engineering app separation that was started in B.

**Estimated Effort:** 2-3 days

---

### 2.5 App: SALES

**Branch:** `feature/sales-from-B`

**Purpose:** Customers, rigs, wells, sales orders, drilling runs, bit lifecycle, shipments.

**Dependencies:** `core`, `inventory` (for Items)

#### Models to Import (9+ models from `floor_app/operations/sales/models/`):

| Model | File | Purpose | Import? |
|-------|------|---------|---------|
| Customer | customer.py | Customer management | ✅ Yes |
| Rig | customer.py | Rig information | ✅ Yes |
| Well | customer.py | Well information | ✅ Yes |
| SalesOpportunity | sales.py | Sales pipeline | ✅ Yes |
| SalesOrder | sales.py | Orders | ✅ Yes |
| SalesOrderLine | sales.py | Order lines | ✅ Yes |
| DrillingRun | drilling.py | Drilling run tracking | ✅ Yes |
| DullGradeEvaluation | dullgrade.py | Dull grading | ✅ Yes |
| BitLifecycleEvent | lifecycle.py | Lifecycle tracking | ✅ Yes |
| Shipment | lifecycle.py | Shipments | ✅ Yes |
| JunkSale | lifecycle.py | Junk sales | ✅ Yes |

#### Views to Import:

From `floor_app/operations/sales/views.py` (903 lines):
- ✅ Customer CRUD
- ✅ Rig and well management
- ✅ Sales order management
- ✅ Drilling run tracking
- ✅ Lifecycle event tracking
- ✅ Shipment management

#### Templates to Import:

**From:** `floor_app/operations/sales/templates/sales/` (44 templates, canonical)
- ✅ Customer templates
- ✅ Rig and well templates
- ✅ Sales order templates
- ✅ Drilling run templates
- ✅ Lifecycle templates
- ✅ Shipment templates

#### URLs:

From `floor_app/operations/sales/urls.py`:
- ✅ All sales URL patterns (namespace: `sales:`)
- ✅ Approximately 74 URLs

#### Migration Steps:

1. Create app: `apps/sales/`
2. Copy models
3. Copy views
4. Copy 44 templates
5. Copy URLs
6. Add to `INSTALLED_APPS`
7. Create migrations
8. Test: Customer creation, sales orders, drilling runs
9. Commit

**Estimated Effort:** 2-3 days

---

### 2.6 Foundation Apps Summary

| App | Priority | Effort | Dependencies | Status |
|-----|----------|--------|--------------|--------|
| core | 1 | 1-2 days | None | ⏳ Pending |
| hr | 2 | 3-4 days | core | ⏳ Pending |
| inventory | 3 | 3-4 days | core | ⏳ Pending |
| engineering | 4 | 2-3 days | inventory | ⏳ Pending |
| sales | 5 | 2-3 days | core, inventory | ⏳ Pending |

**Total Foundation Apps Effort:** 11-16 days (2.5-3.5 weeks)

---

## 3. SUPPORTING APPS MIGRATION

After foundation apps are in place, migrate supporting apps.

### 3.1 Supporting Apps List

| App | Purpose | Models | Effort | Priority |
|-----|---------|--------|--------|----------|
| qrcodes | QR code system | 5 | 1-2 days | High |
| quality | NCR, calibration | 8 | 2-3 days | High |
| maintenance | Asset maintenance | 13 | 2-3 days | Medium |
| purchasing | Procurement | Multiple | 2-3 days | Medium |
| planning | Planning, metrics | 2 | 1-2 days | Medium |
| knowledge | Knowledge base | 19 | 2-3 days | Low |
| analytics | Metrics, monitoring | 10 | 1-2 days | Low |

### 3.2 Migration Approach

For each supporting app:
1. Create feature branch
2. Import models, views, templates (app-specific only)
3. Import URLs
4. Create migrations
5. Test basic functionality
6. Commit and push

**Total Supporting Apps Effort:** 11-17 days (2.5-3.5 weeks)

---

## 4. UNIFIED PRODUCTION & EVALUATION

**This is the critical architectural improvement from Phase 1 findings.**

### 4.1 Problem Statement (from Phase 1)

**In old repo (B):**
- ❌ Production app has: `NdtReport`, `ApiThreadInspection`, `JobCutterEvaluation*`
- ❌ Evaluation app has: `NDTInspection`, `ThreadInspection`, `EvaluationSession/Cell`
- ❌ **Duplicate systems** for same functionality with different data models
- ❌ **Data fragmentation** - same information stored in multiple places
- ❌ **User confusion** - which system to use?

### 4.2 Solution Design for C

**In new repo (C):**

#### Evaluation App - CANONICAL for all inspections/evaluations
- ✅ `EvaluationSession` - Main evaluation record
- ✅ `EvaluationCell` - Grid-based cutter evaluation
- ✅ `NDTInspection` - All NDT (MPI, LPI, UT, etc.)
- ✅ `ThreadInspection` - API thread inspection
- ✅ `TechnicalInstructionTemplate/Instance` - Technical instructions
- ✅ `RequirementTemplate/Instance` - Requirements tracking
- ✅ Supporting models: `CutterEvaluationCode`, `FeatureCode`, `BitSection`, `BitType`

#### Production App - Job execution and routing
- ✅ `JobCard` - Main work order
- ✅ `BatchOrder` - Batch processing
- ✅ `JobRoute`, `JobRouteStep` - Routing and process steps
- ✅ `JobChecklistInstance`, `JobChecklistItem` - Checklists
- ✅ `Quotation`, `QuotationLine` - Quotations
- ✅ **NO** duplicate inspection models
- ✅ **Foreign Key:** `JobCard.evaluation_session` → `EvaluationSession`

### 4.3 Data Model Relationships

```
JobCard (Production)
├── FK → BitDesignRevision (Engineering)
├── FK → Customer (Sales)
├── FK → Rig, Well (Sales)
├── FK → HREmployee (HR) - assigned operator
├── FK → CostCenter (Core)
└── FK → EvaluationSession (Evaluation) ← NEW LINK

EvaluationSession (Evaluation)
├── FK → BitDesign (Engineering)
├── FK → HREmployee (HR) - evaluator
├── One-to-Many → EvaluationCell (cutter grid)
├── One-to-Many → NDTInspection
├── One-to-Many → ThreadInspection
├── One-to-Many → TechnicalInstructionInstance
└── One-to-Many → RequirementInstance
```

### 4.4 URL Structure in C

**Production URLs:**
```
/production/jobcards/                    → Job card list
/production/jobcards/<pk>/               → Job card detail
/production/jobcards/<pk>/routing/       → Routing editor
/production/jobcards/<pk>/checklists/    → Checklists
/production/jobcards/<pk>/evaluation/    → REDIRECT to evaluation app
/production/batches/                     → Batch management
```

**Evaluation URLs:**
```
/evaluation/sessions/                      → Evaluation list
/evaluation/sessions/<pk>/                 → Evaluation detail
/evaluation/sessions/<pk>/grid/            → Cutter grid editor
/evaluation/sessions/<pk>/ndt/             → NDT inspections
/evaluation/sessions/<pk>/thread/          → Thread inspection
/evaluation/sessions/<pk>/instructions/    → Technical instructions
/evaluation/sessions/<pk>/requirements/    → Requirements
/evaluation/sessions/<pk>/review/          → Engineer review
/evaluation/sessions/<pk>/print/           → Print views
```

### 4.5 Template Organization

**Production Templates:**
```
apps/production/templates/production/
├── jobcards/
│   ├── list.html (371 lines - use rich version from B)
│   ├── detail.html
│   └── form.html
├── routing/
│   ├── editor.html
│   ├── add_step.html
│   └── complete_step.html
├── checklists/
│   ├── list.html
│   ├── detail.html
│   └── form.html (create - missing in B)
├── batches/
│   └── ... (standard CRUD)
└── dashboard.html
```

**Evaluation Templates:**
```
apps/evaluation/templates/evaluation/
├── sessions/
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── grid/
│   └── editor.html ← FIX: was sessions/grid_editor.html in B
├── ndt/
│   └── form.html ← FIX: was sessions/ndt_inspection.html in B
├── thread/
│   └── form.html ← FIX: was sessions/thread_inspection.html in B
├── instructions/
│   └── list.html ← FIX: was sessions/instructions.html in B
├── requirements/
│   └── list.html ← FIX: was sessions/requirements.html in B
├── review/
│   └── engineer.html ← FIX: was sessions/engineer_review.html in B
├── print/
│   ├── job_card.html ← FIX: was sessions/print_job_card.html in B
│   └── summary.html ← FIX: was sessions/print_summary.html in B
├── settings/
│   └── ... (codes, features, sections, types)
└── dashboard.html
```

**Critical:** Fix the 8 template path mismatches identified in Phase 1 during migration.

### 4.6 Migration Strategy

**Branch:** `feature/unified-production-evaluation`

**Steps:**

1. **Create Evaluation App in C (Week 4-5):**
   - Import models from `floor_app/operations/evaluation/models/`
   - Create views (from B, review and clean)
   - **Fix template paths** - correct the 8 mismatches
   - Import templates with corrected paths
   - Create URLs
   - Test: Grid editor, NDT form, thread form, all features

2. **Create Production App in C (Week 5):**
   - Import `JobCard`, `BatchOrder`, `JobRoute*` models
   - Import checklist models
   - Import routing models
   - **Add FK:** `evaluation_session` to `JobCard` model
   - Import views (do NOT import NDT/Thread/CutterEval views)
   - Import templates (371-line job card list, routing editor)
   - Create URLs
   - **Link production → evaluation** in views and templates

3. **Integration Testing (Week 5-6):**
   - Create job card
   - Create linked evaluation session
   - Record cutter evaluation in grid
   - Add NDT inspection
   - Add thread inspection
   - Complete evaluation
   - Update job card status
   - Print job card
   - **Verify:** No TemplateDoesNotExist errors
   - **Verify:** Data flows correctly between apps

4. **User Acceptance:**
   - Have domain expert test workflows
   - Verify all features work as expected
   - Adjust based on feedback

**Estimated Effort:** 2-3 weeks

**Risk Level:** HIGH (affects core workflow)
**Mitigation:** Extensive testing, gradual rollout

---

## 5. DOCUMENTATION MIGRATION

### 5.1 Documents to Import (from Phase 1 "KEEP" list)

**Architecture & Design (5 docs):**
- ✅ fms_structure_overview.md → ARCHITECTURE.md (update for C)
- ✅ README_FOR_ROSA.md → Integrate into ARCHITECTURE.md
- ✅ DOCKER_SETUP.md → DEPLOYMENT.md
- ✅ RUNNING_SERVER.md → Integrate into DEPLOYMENT.md
- ✅ TROUBLESHOOTING.md → Keep as-is, update

**Feature Documentation (5 docs):**
- ✅ docs/FEATURES_IMPLEMENTED.md → Keep, update progress
- ✅ docs/VIEW_IMPLEMENTATION_GUIDE.md → DEVELOPER_GUIDE.md
- ✅ DEPARTMENTS_SETUP.md → Keep
- ✅ REQUIREMENTS_SYSTEM_GUIDE.md → Keep
- ✅ VISUAL_PLANNING_DASHBOARD_GUIDE.md → Keep

**Implementation Guides (4 docs):**
- ✅ EXCEL_ANALYSIS_PART3_IMPLEMENTATION.md → Keep as reference
- ✅ EXCEL_INTEGRATION_GAP_ANALYSIS.md → Keep
- ✅ EXCEL_INTEGRATION_SUMMARY.md → Keep
- ✅ ANALYTICS_IMPLEMENTATION_GUIDE.md → Keep

**Health & Quality (2 docs):**
- ✅ HEALTH_CHECK_COMPLETE.md → Archive (specific to B)
- ✅ IMPROVEMENTS.md → Extract relevant parts

**Model & Architecture (5 docs):**
- ✅ FIELD_DUPLICATION_ANALYSIS.md → Reference during migration
- ✅ PROGRESS_MODEL_OWNERSHIP.md → Archive (B-specific)
- ✅ TASK_OWNERSHIP_AND_ORG_STRUCTURE.md → Keep requirements
- ✅ ERRORS_FIXED_AND_PREVENTION.md → BEST_PRACTICES.md
- ✅ NCR_FINANCIAL_MIGRATION_GUIDE.md → Keep

**Phase 1 & 2 (3 docs):**
- ✅ PHASE_1_AUDIT.md → Keep for reference
- ✅ PHASE_2_PROMPT.md → Keep for reference
- ✅ PHASE2_MIGRATION_PLAN.md → This document

### 5.2 New Documentation to Create

**Essential Docs:**
1. **README.md** - Project overview, quick start
2. **CONTRIBUTING.md** - How to contribute
3. **DEPLOYMENT.md** - Production deployment guide
4. **TESTING.md** - Testing strategy and guides
5. **API_DOCUMENTATION.md** - REST API reference
6. **CHANGELOG.md** - Version history
7. **DOCUMENTATION_INDEX.md** - Master index

**Developer Docs:**
8. **DEVELOPER_GUIDE.md** - Code standards, patterns
9. **DATABASE_SCHEMA.md** - Database design
10. **ARCHITECTURE.md** - System architecture

### 5.3 Documentation Structure in C

```
docs/
├── README.md                              # Main project readme
├── DOCUMENTATION_INDEX.md                 # Master index
├── CONTRIBUTING.md                        # Contribution guide
├── CHANGELOG.md                           # Version history
│
├── getting-started/
│   ├── QUICK_START.md
│   ├── INSTALLATION.md
│   └── TROUBLESHOOTING.md
│
├── architecture/
│   ├── ARCHITECTURE.md                    # System overview
│   ├── DATABASE_SCHEMA.md                 # DB design
│   ├── APP_STRUCTURE.md                   # App organization
│   └── UNIFIED_EVALUATION_DESIGN.md       # Production/Evaluation design
│
├── developer/
│   ├── DEVELOPER_GUIDE.md                 # Dev standards
│   ├── TESTING.md                         # Testing guide
│   ├── API_DOCUMENTATION.md               # API reference
│   └── BEST_PRACTICES.md                  # Code quality
│
├── features/
│   ├── DEPARTMENTS_SETUP.md
│   ├── REQUIREMENTS_SYSTEM_GUIDE.md
│   ├── VISUAL_PLANNING_DASHBOARD_GUIDE.md
│   └── FEATURES_IMPLEMENTED.md
│
├── deployment/
│   ├── DEPLOYMENT.md                      # Production deployment
│   ├── DOCKER_SETUP.md                    # Docker guide
│   └── BACKUP_RESTORE.md                  # Backup procedures
│
├── migration/
│   ├── PHASE_1_AUDIT.md                   # From B
│   ├── PHASE_2_PROMPT.md                  # From B
│   ├── PHASE2_MIGRATION_PLAN.md           # This doc
│   └── EXCEL_INTEGRATION_SUMMARY.md       # From B
│
└── reference/
    ├── NCR_FINANCIAL_MIGRATION_GUIDE.md
    ├── QAS105_ORGANIZATION_STRUCTURE_GUIDE.md
    └── EXCEL_ANALYSIS_PART3_IMPLEMENTATION.md
```

**Estimated Effort:** 3-4 days

---

## 6. TESTING INFRASTRUCTURE

### 6.1 Testing Stack

```python
# requirements.txt
pytest==7.4.0
pytest-django==4.5.2
pytest-cov==4.1.0
pytest-xdist==3.3.1  # Parallel testing
factory-boy==3.3.0   # Test factories
faker==19.3.1        # Fake data
coverage==7.3.0
```

### 6.2 Test Structure

```
tests/
├── conftest.py                  # Pytest configuration
├── factories/                   # Test data factories
│   ├── __init__.py
│   ├── core.py
│   ├── hr.py
│   ├── inventory.py
│   ├── engineering.py
│   ├── sales.py
│   ├── production.py
│   └── evaluation.py
│
├── unit/                        # Unit tests
│   ├── test_core_models.py
│   ├── test_hr_models.py
│   ├── test_inventory_models.py
│   ├── test_engineering_models.py
│   └── ...
│
├── integration/                 # Integration tests
│   ├── test_job_card_workflow.py
│   ├── test_evaluation_workflow.py
│   ├── test_inventory_transactions.py
│   └── ...
│
└── api/                         # API tests
    ├── test_core_api.py
    ├── test_hr_api.py
    ├── test_inventory_api.py
    └── ...
```

### 6.3 Test Coverage Goals

| App | Target Coverage | Priority |
|-----|----------------|----------|
| core | 80% | High |
| hr | 70% | High |
| inventory | 75% | High |
| engineering | 75% | High |
| sales | 70% | Medium |
| production | 80% | Critical |
| evaluation | 80% | Critical |
| Other apps | 60% | Medium |

### 6.4 Test Examples

**Model Tests:**
```python
# tests/unit/test_inventory_models.py
import pytest
from apps.inventory.models import Item, ConditionType

@pytest.mark.django_db
def test_item_creation():
    condition = ConditionType.objects.create(code='NEW', name='New')
    item = Item.objects.create(
        item_number='ITEM-001',
        description='Test Item',
        condition=condition
    )
    assert item.item_number == 'ITEM-001'
    assert str(item) == 'ITEM-001 - Test Item'
```

**Integration Tests:**
```python
# tests/integration/test_job_card_workflow.py
import pytest
from apps.production.models import JobCard
from apps.evaluation.models import EvaluationSession

@pytest.mark.django_db
def test_job_card_evaluation_workflow(job_card_factory, evaluation_factory):
    """Test complete job card with linked evaluation"""
    job_card = job_card_factory()
    evaluation = evaluation_factory(job_card=job_card)

    # Record cutter evaluation
    evaluation.add_cutter_cell(cutter_number=1, condition='OK')

    # Add NDT
    ndt = evaluation.add_ndt_inspection(technique='MPI', result='PASS')

    # Add thread inspection
    thread = evaluation.add_thread_inspection(result='ACCEPTABLE')

    # Complete evaluation
    evaluation.complete()

    assert evaluation.status == 'COMPLETED'
    assert job_card.evaluation_session == evaluation
```

**Estimated Effort:** 2 weeks (ongoing, add tests as apps are migrated)

---

## 7. FINAL INTEGRATION

### 7.1 Integration Checklist

**Week 7:**

- [ ] All foundation apps migrated and tested
- [ ] All supporting apps migrated and tested
- [ ] Production + Evaluation unified and tested
- [ ] All documentation created/migrated
- [ ] Test coverage >70% on core apps
- [ ] Database fully migrated
- [ ] Static files organized
- [ ] Media files strategy defined

### 7.2 Full System Testing

**Test Scenarios:**

1. **Complete Job Card Workflow:**
   - Create customer, rig, well
   - Create bit design and BOM
   - Create job card
   - Create linked evaluation
   - Record cutter evaluation
   - Add NDT inspection
   - Add thread inspection
   - Complete evaluation
   - Update job card status
   - Generate reports

2. **HR Workflow:**
   - Create department and position
   - Add employee via wizard
   - Record attendance
   - Request leave
   - Approve leave
   - Track training

3. **Inventory Workflow:**
   - Create items
   - Define locations
   - Record stock receipt
   - Create serial units
   - Track movements
   - Generate reports

4. **Sales Workflow:**
   - Create customer
   - Create sales opportunity
   - Convert to order
   - Link to job card
   - Track drilling run
   - Record lifecycle events

### 7.3 Performance Testing

- [ ] Load test with 1000+ job cards
- [ ] Test concurrent users (10-50)
- [ ] Database query optimization
- [ ] Template rendering performance
- [ ] API endpoint performance

### 7.4 Security Audit

- [ ] Authentication & authorization
- [ ] CSRF protection
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Sensitive data protection
- [ ] API security

### 7.5 Deployment Preparation

- [ ] Production settings configured
- [ ] Environment variables documented
- [ ] Database backup strategy
- [ ] Static files collection tested
- [ ] Gunicorn configuration
- [ ] Nginx configuration (if needed)
- [ ] SSL certificates
- [ ] Monitoring setup

**Estimated Effort:** 1 week

---

## 8. SUCCESS CRITERIA

### 8.1 Technical Criteria

- ✅ All apps from B migrated to C (selective, canonical implementations only)
- ✅ Zero duplicate models (108+ models, all unique)
- ✅ Zero orphaned templates (only canonical templates imported)
- ✅ Unified evaluation system (no duplicate inspection models)
- ✅ Django check passes with 0 errors
- ✅ All migrations run successfully
- ✅ Test coverage >70% on core apps
- ✅ API documentation complete
- ✅ Deployment guide tested

### 8.2 Functional Criteria

- ✅ Job card workflow works end-to-end
- ✅ Evaluation workflow integrated with production
- ✅ Inventory management functional
- ✅ HR system complete (employees, leave, attendance, training)
- ✅ Sales and customer management works
- ✅ All CRUD operations tested
- ✅ Reports generate correctly
- ✅ Search functionality works
- ✅ QR code integration functional

### 8.3 Quality Criteria

- ✅ No technical debt from old system
- ✅ Clean, maintainable code structure
- ✅ Comprehensive documentation
- ✅ Test infrastructure in place
- ✅ CI/CD ready
- ✅ Performance acceptable (< 2s page load)
- ✅ Security best practices followed
- ✅ Accessibility considered

### 8.4 Business Criteria

- ✅ All critical features from B available in C
- ✅ User workflows improved (unified evaluation)
- ✅ Data integrity maintained
- ✅ System ready for production use
- ✅ Training materials available
- ✅ Support documentation complete

---

## 9. TIMELINE SUMMARY

| Phase | Tasks | Weeks | Cumulative |
|-------|-------|-------|------------|
| **Pre-Migration** | Setup, planning | 0.5 | 0.5 |
| **Foundation Apps** | core, hr, inventory, engineering, sales | 2.5-3.5 | 3-4 |
| **Supporting Apps** | qrcodes, quality, maintenance, etc. | 2.5-3.5 | 5.5-7.5 |
| **Production + Evaluation** | Unified system | 2-3 | 7.5-10.5 |
| **Documentation** | All docs | 0.5-1 | 8-11.5 |
| **Testing** | Test infrastructure (ongoing) | 2 | 10-13.5 |
| **Final Integration** | Testing, deployment prep | 1 | 11-14.5 |
| **Buffer** | Unexpected issues | 0.5-1 | 11.5-15.5 |

**Total Estimated Timeline:** 11.5 - 15.5 weeks (approximately 3-4 months)

**Realistic Delivery:** 3.5 months with one full-time developer

---

## 10. NEXT STEPS

### Immediate Actions

1. **Confirm Prerequisites:**
   - [ ] C repo accessible
   - [ ] PostgreSQL database `floor_management_c` created
   - [ ] Django 5.2.6 project initialized
   - [ ] Git connected to GitHub remote

2. **Start Foundation Apps:**
   - [ ] Create `feature/core-from-B` branch
   - [ ] Begin core app migration
   - [ ] Document progress in `docs/PHASE2_PROGRESS.md`

3. **Report First Milestone:**
   - After core + inventory (or core + hr) complete
   - Pause for review
   - Adjust plan based on learnings

### Questions to Resolve

- [ ] What is the GitHub URL for C repo?
- [ ] PostgreSQL connection details confirmed?
- [ ] Any specific customizations needed?
- [ ] Who will review migrations?
- [ ] Timeline constraints?

---

**Document Created:** 2025-11-22
**Status:** Ready for Execution
**Next Action:** Begin core app migration after C repo access confirmed

---

**END OF MIGRATION PLAN**

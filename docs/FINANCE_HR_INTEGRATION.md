# Finance/ERP Integration & Enhanced HRMS Documentation

## Overview

This document describes the comprehensive Finance/ERP Integration layer and Enhanced HRMS capabilities implemented in the Floor Management System. The system provides:

1. **User Preferences & UI Customization** - Persistent theme, font size, and table density preferences
2. **Global Reusable Table Component** - Full-featured data tables with sorting, filtering, pagination
3. **ERP Reference Mapping** - Generic and specific ERP number storage and linking
4. **Cost Center Management** - Organizational units for financial tracking
5. **Loss of Sale Tracking** - Financial impact monitoring
6. **Approval Routing** - Configurable approval authorities
7. **Django Core Tables Front-End** - Non-admin views for system tables

---

## Architecture & Data Model

### 1. User Preferences (core.UserPreference)

**Purpose:** Store per-user UI customization settings.

**Fields:**
- `user` - OneToOne link to auth.User
- `theme` - light/dark/high_contrast
- `font_size` - small/normal/large
- `table_density` - compact/normal/relaxed
- `default_landing_page` - URL name for post-login redirect
- `table_columns_config` - JSON field storing per-view column visibility
- `sidebar_collapsed`, `sidebar_sections` - UI state persistence
- `email_notifications`, `desktop_notifications` - Notification preferences

**Integration Points:**
- Context processor injects preferences into all templates
- JavaScript API for saving column preferences
- Live theme preview in settings page

---

### 2. ERP Reference Mapping Strategy

**Philosophy:** Use a hybrid approach:
- **Direct fields** on critical models for primary ERP numbers (fast queries, clear ownership)
- **Generic ERPReference table** for multiple/secondary references (flexibility, audit trail)

#### Direct ERP Fields Added:

**JobCard:**
```python
erp_production_order_number = CharField(max_length=50)
cost_center = ForeignKey('core.CostCenter')
```

**BitDesignRevision (MAT):**
```python
erp_item_number = CharField(max_length=50)  # ERP Material Code
erp_bom_number = CharField(max_length=50)
standard_cost = DecimalField(max_digits=12, decimal_places=2)
last_purchase_cost = DecimalField(max_digits=12, decimal_places=2)
```

**BOMHeader:**
```python
erp_bom_number = CharField(max_length=50)
total_material_cost = DecimalField(max_digits=12, decimal_places=2)
```

**Department:**
```python
cost_center = ForeignKey('core.CostCenter')
erp_department_code = CharField(max_length=50)
```

**HREmployee:**
```python
cost_center = ForeignKey('core.CostCenter')
grade = CharField(max_length=20)
supervisor = ForeignKey('self')
overtime_eligible = BooleanField()
```

#### Generic ERP Reference (core.ERPReference)

**Purpose:** Link any internal object to any ERP document with full audit trail.

**Structure:**
```python
content_type = ForeignKey(ContentType)  # What type of internal object
object_id = BigIntegerField()           # ID of internal object
document_type = ForeignKey(ERPDocumentType)  # PR, PO, GRN, TO, etc.
erp_number = CharField(max_length=100)
erp_line_number = IntegerField(null=True)
erp_date = DateField(null=True)
erp_status = CharField()
erp_json_data = JSONField()  # Additional ERP metadata
sync_status = CharField()  # pending/synced/error/manual
```

**ERP Document Types Supported:**
- PR - Purchase Requisition
- PO - Purchase Order
- GRN - Goods Receipt Note
- TO - Transfer Order
- PICK - Picking List
- INV - Invoice
- PROD - Production Order
- CUST - Customer
- ITEM - Item/Material Code
- BOM - Bill of Materials

**Usage Example:**
```python
# Link a JobCard to an ERP Production Order
from core.models import ERPReference, ERPDocumentType
from django.contrib.contenttypes.models import ContentType

job_card = JobCard.objects.get(pk=123)
prod_order_type = ERPDocumentType.objects.get(code='PROD')

ERPReference.objects.create(
    content_type=ContentType.objects.get_for_model(job_card),
    object_id=job_card.pk,
    document_type=prod_order_type,
    erp_number='PROD-2025-001234',
    sync_status='manual',
    created_by=request.user
)
```

---

### 3. Cost Center Management (core.CostCenter)

**Purpose:** Financial tracking and KPI analysis across the organization.

**Features:**
- Hierarchical structure (parent/child)
- ERP integration (`erp_cost_center_code`)
- Budget tracking (`annual_budget`, `currency`)
- Manager assignment
- Status tracking (active/inactive/archived)

**Linked To:**
- Departments
- Employees
- Job Cards
- Loss of Sale Events
- Approval Authorities

**Use Cases:**
- Track costs per production area
- Allocate expenses to specific teams
- Generate P&L by cost center
- KPI reporting by organizational unit

---

### 4. Loss of Sale Tracking (core.LossOfSaleEvent)

**Purpose:** Record and analyze incidents causing missed or delayed sales.

**Key Fields:**
- `reference_number` - Auto-generated (LOS-000001)
- `cause` - Linked to LossOfSaleCause (categorized: stockout, breakdown, delay, quality, logistics, external)
- `event_date`, `duration_hours`
- `estimated_loss_amount`, `currency`
- `calculation_method` - How loss was estimated
- `cost_center` - Affected cost center
- Generic FK to related object (JobCard, Asset, etc.)
- `root_cause_analysis`, `corrective_actions`, `preventive_measures`
- Workflow: draft → submitted → reviewed → approved

**Reporting Capabilities:**
- Total loss by period
- Loss breakdown by cause category
- Loss by cost center
- Trend analysis

---

### 5. Approval Routing (core.ApprovalAuthority)

**Purpose:** Define who can approve what based on amount limits and organizational structure.

**Structure:**
```python
approval_type = ForeignKey(ApprovalType)  # PR, PO, JobCard, Maintenance
user = ForeignKey(User)  # OR
group = ForeignKey(Group)  # OR
position_id = BigIntegerField()  # HR Position
min_amount = DecimalField()
max_amount = DecimalField()  # null = unlimited
cost_center = ForeignKey(CostCenter)  # Scope limitation
priority = IntegerField()  # Routing order
```

**Approval Types:**
- PR - Purchase Requisition approval
- PO - Purchase Order approval
- JOB - Job Card approval
- MAINT - Maintenance Request approval
- LOS - Loss of Sale event approval

**Future Integration:**
- Workflow engine to route approvals
- Email notifications
- Escalation rules

---

### 6. Global Table Component

**Location:** `core/templates/core/partials/data_table.html`

**Features:**
- **Sorting** - Click column headers, multi-column support
- **Search** - Global search with debounced input
- **Filtering** - Per-column filters (select, date range)
- **Pagination** - Server-side with page size selector (10/25/50/100)
- **Column Visibility** - Toggle columns, save preferences
- **Bulk Actions** - Select multiple rows, delete/export
- **Row Actions** - View/Edit/Delete buttons per row
- **Mobile Responsive** - Card view on small screens
- **Theme Aware** - Adapts to light/dark/high-contrast

**JavaScript:** `core/static/core/js/data-table.js`
- Column preference persistence (localStorage + API)
- Dynamic sorting/filtering via URL params
- Export functionality (CSV, Excel, PDF)
- Toast notifications

**Template Tags:** `core/templatetags/core_tags.py`
- `get_attr` - Nested attribute access
- `get_item` - Dictionary item access
- `format_currency` - Currency formatting
- `status_badge_class` - Status-based badge styling
- `erp_reference_badge` - Display ERP references inline

---

### 7. Theme System

**CSS:** `core/static/core/css/themes.css`

**Three Complete Themes:**
1. **Light Mode** (default)
   - White/light gray backgrounds
   - Dark text
   - Subtle shadows and gradients

2. **Dark Mode**
   - Dark blue/gray backgrounds
   - Light text
   - Purple accent colors

3. **High Contrast** (Accessibility)
   - Black background
   - White text
   - Yellow accents
   - Strong borders
   - Focus indicators

**Font Size Options:**
- Small (13px base)
- Normal (16px base)
- Large (18px base)

**Table Density:**
- Compact (0.4rem padding)
- Normal (0.75rem padding)
- Relaxed (1.25rem padding)

**Integration:**
- Body classes: `theme-light`, `ui-font-normal`, `table-density-normal`
- Context processor injects user preferences
- Real-time preview in settings page

---

### 8. Django Core Tables Front-End

**Purpose:** Professional UI for viewing/editing Django internal tables outside /admin/.

**Views Available:**
- Users (`/system/users/`) - List, detail
- Groups (`/system/groups/`) - List, detail
- Permissions (`/system/permissions/`) - List
- Content Types (`/system/content-types/`) - List
- Admin Log (`/system/admin-log/`) - List
- Sessions (`/system/sessions/`) - List

**Features:**
- Staff-only access
- Full search/filter/sort
- Consistent with app styling
- View user groups and permissions
- View group members and permissions

---

## File Structure

```
core/
├── models.py           # All core models
├── views.py            # All views (preferences, finance, Django core)
├── urls.py             # URL routing
├── admin.py            # Admin registrations
├── context_processors.py  # User preferences injection
├── templatetags/
│   └── core_tags.py    # Custom template filters
├── templates/
│   └── core/
│       ├── partials/
│       │   ├── data_table.html    # Global table component
│       │   └── erp_badge.html     # ERP reference badges
│       ├── user_preferences.html  # Settings page
│       ├── finance_dashboard.html # Finance overview
│       └── django_core/           # Django core table views
└── static/
    └── core/
        ├── css/
        │   └── themes.css         # Theme system
        └── js/
            └── data-table.js      # Table interactions
```

---

## How to Search/Query ERP References

### Find Job Card by ERP Production Order:
```python
from core.models import ERPReference
from floor_app.operations.production.models import JobCard
from django.contrib.contenttypes.models import ContentType

# Method 1: Direct field
job_cards = JobCard.objects.filter(erp_production_order_number='PROD-2025-001234')

# Method 2: Generic reference
ct = ContentType.objects.get_for_model(JobCard)
refs = ERPReference.objects.filter(
    document_type__code='PROD',
    erp_number='PROD-2025-001234',
    content_type=ct
)
job_card_ids = refs.values_list('object_id', flat=True)
job_cards = JobCard.objects.filter(pk__in=job_card_ids)
```

### Find All ERP References for an Object:
```python
from core.models import ERPReference
from django.contrib.contenttypes.models import ContentType

job_card = JobCard.objects.get(pk=123)
ct = ContentType.objects.get_for_model(job_card)
refs = ERPReference.objects.filter(
    content_type=ct,
    object_id=job_card.pk
).select_related('document_type')

for ref in refs:
    print(f"{ref.document_type.code}: {ref.erp_number}")
```

---

## Future Enhancements

### API Sync Integration:
```python
# Pseudo-code for ERP API sync
def sync_erp_references():
    pending = ERPReference.objects.filter(sync_status='pending')
    for ref in pending:
        try:
            erp_data = erp_api.fetch(ref.document_type.code, ref.erp_number)
            ref.erp_status = erp_data['status']
            ref.erp_json_data = erp_data
            ref.sync_status = 'synced'
            ref.last_synced = timezone.now()
            ref.save()
        except Exception as e:
            ref.sync_status = 'error'
            ref.sync_error_message = str(e)
            ref.save()
```

### Cost Analysis:
```python
# Calculate material cost for a job
def calculate_job_material_cost(job_card):
    total = Decimal('0.00')

    # Sum consumed inventory
    for transaction in job_card.inventory_transactions.all():
        if transaction.item.last_purchase_cost:
            total += transaction.quantity * transaction.item.last_purchase_cost

    # Add BOM material cost if available
    if job_card.bom and job_card.bom.total_material_cost:
        total += job_card.bom.total_material_cost

    return total
```

---

## Installation Steps

1. **Run Migrations:**
```bash
python manage.py makemigrations core
python manage.py makemigrations hr
python manage.py makemigrations production
python manage.py makemigrations inventory
python manage.py migrate
```

2. **Create Initial Data:**
```bash
python manage.py shell
```
```python
from core.models import ERPDocumentType, LossOfSaleCause, ApprovalType, Currency

# ERP Document Types
ERPDocumentType.objects.bulk_create([
    ERPDocumentType(code='PR', name='Purchase Requisition'),
    ERPDocumentType(code='PO', name='Purchase Order'),
    ERPDocumentType(code='GRN', name='Goods Receipt Note'),
    ERPDocumentType(code='TO', name='Transfer Order'),
    ERPDocumentType(code='PICK', name='Picking List'),
    ERPDocumentType(code='INV', name='Invoice'),
    ERPDocumentType(code='PROD', name='Production Order'),
])

# Loss of Sale Causes
LossOfSaleCause.objects.bulk_create([
    LossOfSaleCause(code='STK-001', name='Raw Material Shortage', category='stockout'),
    LossOfSaleCause(code='STK-002', name='Component Stock Out', category='stockout'),
    LossOfSaleCause(code='BRK-001', name='Equipment Breakdown', category='breakdown'),
    LossOfSaleCause(code='DLY-001', name='Production Delay', category='delay'),
    LossOfSaleCause(code='QTY-001', name='Quality Rejection', category='quality'),
])

# Approval Types
ApprovalType.objects.bulk_create([
    ApprovalType(code='PR', name='Purchase Requisition'),
    ApprovalType(code='PO', name='Purchase Order'),
    ApprovalType(code='JOB', name='Job Card'),
    ApprovalType(code='MAINT', name='Maintenance Request'),
    ApprovalType(code='LOS', name='Loss of Sale Event'),
])

# Currency
Currency.objects.create(
    code='SAR',
    name='Saudi Riyal',
    symbol='SAR',
    is_base_currency=True
)
```

3. **Update Navigation (if needed):**
The sidebar in `base.html` already includes links to Finance and System Administration sections.

---

## Testing the Implementation

1. **User Preferences:**
   - Log in and go to Settings
   - Change theme to Dark Mode
   - Adjust font size and table density
   - Verify changes persist across page reloads

2. **Finance Dashboard:**
   - Navigate to `/finance/`
   - Verify summary metrics
   - Check document type listing
   - Create test loss of sale event

3. **ERP References:**
   - Use admin to create ERPReference records
   - Link to existing JobCards or other objects
   - Verify they appear in ERP References list

4. **Cost Centers:**
   - Create cost centers with hierarchy
   - Assign to departments and employees
   - Link job cards to cost centers

5. **Table Component:**
   - Test sorting by clicking headers
   - Test search functionality
   - Toggle column visibility
   - Save column preferences
   - Test pagination

---

## Conclusion

This implementation provides a robust foundation for ERP integration without duplicating ERP functionality. The system maintains Django as the source of truth for floor operations while bridging to external ERP systems through well-structured reference links.

Key benefits:
- **Non-duplicated data** - Single source of truth per domain
- **Searchable** - Fast queries on ERP numbers
- **Auditable** - Full history of ERP references
- **Extensible** - Easy to add API sync later
- **User-friendly** - Professional UI with customization
- **Responsive** - Works on desktop and mobile
- **Accessible** - High-contrast theme option

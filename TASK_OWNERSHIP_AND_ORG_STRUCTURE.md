# Task: Fix Model Ownership and Set Up Organization Structure

## IMPORTANT: Error Prevention Guidelines

**Before starting this task, review these documents:**
- `ERRORS_FIXED_AND_PREVENTION.md` - Comprehensive error prevention guide
- `fms_structure_overview.md` - Current system architecture
- `model_ownership_mapping.csv` - Current model ownership analysis

**Critical patterns to follow from the error prevention guide:**

### 1. Import Management (See ERRORS_FIXED_AND_PREVENTION.md Section 1)
```python
# ✅ Use string references to avoid circular imports
department = models.ForeignKey('Department', on_delete=models.PROTECT)

# ✅ Always use absolute imports for cross-app references
from floor_app.operations.engineering.models import BitDesign

# ✅ Import timezone explicitly
from django.utils import timezone
```

### 2. Model Relationships (See ERRORS_FIXED_AND_PREVENTION.md Section 2)
```python
# ✅ Always add related_name to ForeignKeys
position = models.ForeignKey(
    Position,
    on_delete=models.PROTECT,
    related_name='employees'
)

# ✅ Use PROTECT for critical business relationships
ncr = models.ForeignKey(
    'quality.NonconformanceReport',
    on_delete=models.PROTECT
)
```

### 3. Mandatory Checks After Changes (See ERRORS_FIXED_AND_PREVENTION.md Section "Before Every Commit")
```bash
# Run these after EVERY change:
python manage.py check
python manage.py makemigrations --dry-run
python manage.py makemigrations
python manage.py migrate
```

### 4. Systematic Updates (See ERRORS_FIXED_AND_PREVENTION.md "Model Changes Checklist")
When moving models, you MUST update in this order:
1. ✅ Move model files
2. ✅ Update model imports in __init__.py
3. ✅ Update all forms that use the model
4. ✅ Update admin.py registrations
5. ✅ Update views that import the model
6. ✅ Update serializers (if using DRF)
7. ✅ Update templates that reference the model
8. ✅ Update URL patterns
9. ✅ Create migrations with proper db_table names
10. ✅ Run migrations
11. ✅ Run python manage.py check

---

## Task Overview

You are working on the Django/PostgreSQL project **floor_management_system-B**.

**Your task in this run is ONLY:**

1. Fix wrong ownership of key models (which app/department they belong to)
2. Set up a clean Department & Position structure based on our official QAS-105 job titles document and current practice

**Work in a new Git branch:** `feat/ownership-and-org-structure`

---

## PART 1: Fix Model Ownership / Module Boundaries

### Context

**Current analysis:**
- `fms_structure_overview.md` and `README_FOR_ROSA.md` identified misplaced models
- `model_ownership_mapping.csv` contains detailed ownership analysis

**Misplaced models identified:**
- **Bit design & BOM models** are currently in `floor_app/operations/inventory/models/` (WRONG)
  - BitDesign, BitDesignRevision
  - BOMHeader, BOMLine
  - RollerConeDesign, RollerConeBOM

- **Quality NCR** contains financial fields (WRONG from separation-of-duties perspective)
  - estimated_cost_impact, actual_cost_impact, lost_revenue

**Business rules:**
- **Technical/Engineering** owns designs and BOM definitions (what is needed to build/repair a bit at design level)
- **Production/Operations** owns routing, operations, job cards, actual work execution
- **Inventory/Supply Chain** owns stock, locations, issues/receipts, reservations (NOT design/BOM logic)
- **Quality** owns NCR, inspections, checklists (NOT cost/price numbers)
- **Finance** owns cost, price, and financial impact calculations

---

### 1.1 Create Engineering App and Move Design/BOM Models

**⚠️ CRITICAL: Follow ERRORS_FIXED_AND_PREVENTION.md Section 2 & Section 9 (Migrations)**

#### Step 1: Create Engineering App Structure

```bash
# Create the engineering app directory structure
mkdir -p floor_app/operations/engineering/models
mkdir -p floor_app/operations/engineering/admin
mkdir -p floor_app/operations/engineering/views
mkdir -p floor_app/operations/engineering/forms
mkdir -p floor_app/operations/engineering/migrations
```

Create required files:
- `floor_app/operations/engineering/__init__.py`
- `floor_app/operations/engineering/apps.py`
- `floor_app/operations/engineering/models/__init__.py`
- `floor_app/operations/engineering/admin/__init__.py`
- `floor_app/operations/engineering/migrations/__init__.py`

Add to `INSTALLED_APPS` in settings:
```python
INSTALLED_APPS = [
    # ...
    'floor_app.operations.engineering',
    # ...
]
```

#### Step 2: Move Models from Inventory to Engineering

**⚠️ IMPORTANT: Use db_table to preserve database tables**

**Models to move:**
1. From `floor_app/operations/inventory/models/bit_design.py`:
   - BitDesignLevel
   - BitDesignType
   - BitDesign
   - BitDesignRevision

2. From `floor_app/operations/inventory/models/bom.py`:
   - BOMHeader
   - BOMLine

3. From `floor_app/operations/inventory/models/roller_cone.py`:
   - RollerConeBitType
   - RollerConeBearing
   - RollerConeSeal
   - RollerConeDesign
   - RollerConeComponent
   - RollerConeBOM

**Process:**

```python
# ⚠️ In each moved model, keep the db_table to preserve data
class BitDesign(models.Model):
    # ... fields ...

    class Meta:
        db_table = 'inventory_bitdesign'  # Keep original table name
        # ... other meta options
```

**⚠️ Follow the systematic update checklist from ERRORS_FIXED_AND_PREVENTION.md:**

1. **Move model files** to `floor_app/operations/engineering/models/`
2. **Create new __init__.py** in engineering/models/ with proper imports
3. **Update inventory models __init__.py** - remove moved model imports
4. **Find and update ALL imports** across the codebase:
   ```bash
   # Search for old imports
   grep -r "from floor_app.operations.inventory.models import.*BitDesign" .
   grep -r "from floor_app.operations.inventory.models import.*BOM" .

   # Replace with new imports
   from floor_app.operations.engineering.models import BitDesign, BOMHeader
   ```

5. **Move admin registrations**:
   - From `floor_app/operations/inventory/admin.py`
   - To `floor_app/operations/engineering/admin/`
   - **⚠️ Update admin imports** (See ERRORS_FIXED_AND_PREVENTION.md Section 4)

6. **Move forms**:
   - Find forms in `floor_app/operations/inventory/forms.py` that use moved models
   - Move to `floor_app/operations/engineering/forms.py`
   - **⚠️ Update form imports** and Meta.model references

7. **Move views**:
   - Find views in `floor_app/operations/inventory/views/` that handle moved models
   - Move to `floor_app/operations/engineering/views/`
   - **⚠️ Update view imports** (See ERRORS_FIXED_AND_PREVENTION.md Section 6)

8. **Move URL patterns**:
   - Extract URL patterns from `floor_app/operations/inventory/urls.py`
   - Create `floor_app/operations/engineering/urls.py`
   - Include in main urls.py

9. **Move templates**:
   - From `floor_app/templates/inventory/bit_designs/`
   - To `floor_app/templates/engineering/bit_designs/`
   - From `floor_app/templates/inventory/boms/`
   - To `floor_app/templates/engineering/boms/`
   - **⚠️ Update template references** in views (See ERRORS_FIXED_AND_PREVENTION.md Section 5)

10. **Create migrations**:
    ```bash
    python manage.py makemigrations engineering
    python manage.py makemigrations inventory
    python manage.py migrate
    ```

11. **Verify with Django check**:
    ```bash
    python manage.py check
    ```

**⚠️ Common Mistakes to Avoid (from ERRORS_FIXED_AND_PREVENTION.md):**
- ❌ Don't forget to update serializers if using DRF
- ❌ Don't leave old imports in __init__.py
- ❌ Don't forget related_name in ForeignKeys
- ❌ Don't create circular imports
- ❌ Don't forget to update admin list_display, list_filter, search_fields
- ❌ Don't skip the `python manage.py check` command

**Result:**
- ✅ Engineering app owns design/BOM data
- ✅ Inventory app focuses on items, stock, locations, item movements only

---

### 1.2 Keep Routing & Operations Under Production

**⚠️ CRITICAL: Verify ownership, don't move unnecessarily**

**Business rule:**
- Technology/Engineering does NOT own production routes
- Routes and operation sequences belong to Production
- Quality monitors them, but Production owns them

**Action:**

1. **Verify these models are in `floor_app/operations/production/`:**
   - OperationDefinition / OperationType
   - RoutingTemplate / RoutingOperation
   - JobCard, WorkOrderOperation

2. **If any are misplaced**, follow the same systematic process as 1.1

3. **Do NOT create new routing logic** - just verify ownership

**Result:**
- ✅ Engineering → defines **what** needs to be done (design/BOM, technical instructions)
- ✅ Production → defines **how** & **in which sequence** operations are executed

---

### 1.3 Remove Financial Fields from Quality NCR and Move to Finance

**⚠️ CRITICAL: Follow ERRORS_FIXED_AND_PREVENTION.md Section 2, 9**

**Business rule:**
- QA should log technical and quality information (defect, cause, disposition)
- QA should NOT enter cost/price numbers
- Finance should maintain financial impact

#### Step 1: Locate Current NCR Model

File: `floor_app/operations/quality/models.py` (or similar)

Model: `NonconformanceReport`

**Current financial fields to remove:**
- `estimated_cost_impact`
- `actual_cost_impact`
- `lost_revenue`

#### Step 2: Create Finance Structure (if not exists)

**Option A: Create dedicated finance app** (preferred)
```bash
mkdir -p floor_app/operations/finance/models
mkdir -p floor_app/operations/finance/admin
mkdir -p floor_app/operations/finance/migrations
```

**Option B: Use core app** (if finance app not ready)
```bash
# Create in core/models/
```

#### Step 3: Create NCRFinancialImpact Model

**⚠️ Use proper ForeignKey patterns from ERRORS_FIXED_AND_PREVENTION.md Section 2**

```python
# floor_app/operations/finance/models/ncr_financial.py (or core/models/ncr_financial.py)

from django.db import models
from django.utils import timezone  # ⚠️ Always import timezone
from floor_app.operations.quality.models import NonconformanceReport

class NCRFinancialImpact(models.Model):
    """
    Financial impact tracking for Non-Conformance Reports.
    Separated from QA to maintain separation of duties.
    """
    ncr = models.OneToOneField(
        NonconformanceReport,
        on_delete=models.PROTECT,  # ⚠️ Use PROTECT for critical relationships
        related_name='financial_impact'  # ⚠️ Always add related_name
    )

    # Cost breakdown
    material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Material cost impact"
    )
    labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Labor cost impact"
    )
    scrap_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Scrap/waste cost"
    )
    lost_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Estimated lost revenue"
    )

    # Total
    total_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total financial impact"
    )

    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (USD, EUR, etc.)"
    )

    # Notes
    notes = models.TextField(blank=True, help_text="Financial impact notes")

    # Audit fields - ⚠️ Use timezone.now, not datetime.now
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='ncr_financial_impacts_created'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_ncr_financial_impact'
        verbose_name = 'NCR Financial Impact'
        verbose_name_plural = 'NCR Financial Impacts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Financial Impact for {self.ncr}"

    def save(self, *args, **kwargs):
        # Auto-calculate total
        self.total_impact = (
            self.material_cost +
            self.labor_cost +
            self.scrap_cost +
            self.lost_revenue
        )
        super().save(*args, **kwargs)
```

#### Step 4: Create Data Migration

**⚠️ Follow ERRORS_FIXED_AND_PREVENTION.md Section 9 (Migrations)**

```bash
# Create empty migration
python manage.py makemigrations quality --empty --name migrate_financial_fields_to_finance
```

Edit the migration file:

```python
# floor_app/operations/quality/migrations/XXXX_migrate_financial_fields_to_finance.py

from django.db import migrations

def migrate_financial_data(apps, schema_editor):
    """
    Migrate financial data from NCR to NCRFinancialImpact
    """
    NonconformanceReport = apps.get_model('quality', 'NonconformanceReport')
    NCRFinancialImpact = apps.get_model('finance', 'NCRFinancialImpact')

    for ncr in NonconformanceReport.objects.all():
        # Check if old fields exist and have data
        if hasattr(ncr, 'estimated_cost_impact') or hasattr(ncr, 'actual_cost_impact'):
            NCRFinancialImpact.objects.create(
                ncr=ncr,
                material_cost=getattr(ncr, 'material_cost', 0),
                labor_cost=getattr(ncr, 'labor_cost', 0),
                scrap_cost=getattr(ncr, 'scrap_cost', 0),
                lost_revenue=getattr(ncr, 'lost_revenue', 0),
                created_by=ncr.created_by,
                created_at=ncr.created_at,
                notes=f"Migrated from NCR #{ncr.id}"
            )

def reverse_migration(apps, schema_editor):
    """
    Reverse operation if needed
    """
    NCRFinancialImpact = apps.get_model('finance', 'NCRFinancialImpact')
    NCRFinancialImpact.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('quality', 'XXXX_previous_migration'),
        ('finance', 'XXXX_create_ncr_financial_impact'),
    ]

    operations = [
        migrations.RunPython(migrate_financial_data, reverse_migration),
    ]
```

#### Step 5: Remove Financial Fields from NCR

Edit `floor_app/operations/quality/models.py`:

```python
class NonconformanceReport(models.Model):
    # ... other fields ...

    # ❌ REMOVE these fields:
    # estimated_cost_impact = models.DecimalField(...)
    # actual_cost_impact = models.DecimalField(...)
    # lost_revenue = models.DecimalField(...)

    # ... rest of model ...
```

Create migration:
```bash
python manage.py makemigrations quality --name remove_financial_fields_from_ncr
```

#### Step 6: Update Forms and Views

**⚠️ Follow ERRORS_FIXED_AND_PREVENTION.md Section 3 (Forms) and Section 6 (Views)**

1. **Update NCR forms** (`floor_app/operations/quality/forms.py`):
   ```python
   class NonconformanceReportForm(forms.ModelForm):
       class Meta:
           model = NonconformanceReport
           fields = [
               'ncr_number', 'product', 'description', 'severity',
               'root_cause', 'corrective_action', 'disposition',
               # ❌ DO NOT include financial fields
           ]
           # ⚠️ Verify all fields exist in model
   ```

2. **Update NCR admin** (`floor_app/operations/quality/admin.py`):
   ```python
   class NonconformanceReportAdmin(admin.ModelAdmin):
       list_display = [
           'ncr_number', 'product', 'severity', 'status', 'created_at'
           # ❌ Remove financial fields from list_display
       ]
       list_filter = ['severity', 'status', 'created_at']
       # ❌ Remove financial fields from list_filter
   ```

3. **Create Finance admin** for NCRFinancialImpact:
   ```python
   # floor_app/operations/finance/admin.py
   from django.contrib import admin
   from .models import NCRFinancialImpact

   @admin.register(NCRFinancialImpact)
   class NCRFinancialImpactAdmin(admin.ModelAdmin):
       list_display = [
           'ncr', 'total_impact', 'currency', 'created_by', 'created_at'
       ]
       list_filter = ['currency', 'created_at']
       readonly_fields = ['total_impact', 'created_at', 'updated_at']

       # ⚠️ Only Finance users should access this
       def has_module_permission(self, request):
           return request.user.has_perm('finance.view_ncrfinancialimpact')
   ```

4. **Update NCR detail templates**:
   - Remove financial fields from Quality NCR templates
   - Create separate Finance view for financial impact

#### Step 7: Run Migrations and Verify

```bash
# ⚠️ Always check before migrating
python manage.py check

# Create migrations
python manage.py makemigrations

# Show migration plan
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Verify data migration worked
python manage.py shell
>>> from floor_app.operations.finance.models import NCRFinancialImpact
>>> NCRFinancialImpact.objects.count()
```

**Result:**
- ✅ Quality module is clean, with no cost fields
- ✅ Finance owns and controls all financial impact data
- ✅ Separation of duties maintained

---

## PART 2: Normalize Departments & Positions Based on QAS-105

**⚠️ CRITICAL: Follow ERRORS_FIXED_AND_PREVENTION.md Section 2 for all model work**

### Context

**Existing HR models:**
- `Department` (code, name, parent, manager)
- `Position` (code, title, department, grade_level)
- `HRPeople` or `Employee` (person/employee model)

**Reference document:**
- QAS-105 Job Titles, Responsibilities, Authorities & Accountabilities (ARDT official document)

**Current reality:**
- User's title: "FC Refurbish Supervisor"
- This is functionally the Repair Coordinator/Repair Supervisor role
- Oversees FC repair and new bit production supervision

**Goal:**
- Make `hr.Department` and `hr.Position` the single source of truth
- Match QAS-105 structure + current real titles

---

### 2.1 Create Department Records

**⚠️ Follow model relationship patterns from ERRORS_FIXED_AND_PREVENTION.md Section 2**

#### Step 1: Review Current Department Model

Read: `floor_app/operations/hr/models.py` (or wherever Department is defined)

Ensure model has:
```python
class Department(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_departments'  # ⚠️ Always add related_name
    )
    manager = models.ForeignKey(
        'auth.User',  # or 'HRPeople'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'  # ⚠️ Always add related_name
    )
    is_active = models.BooleanField(default=True)

    # ⚠️ Use timezone.now
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Step 2: Create Department Data Migration

**Departments from QAS-105:**

```python
# Create data migration
python manage.py makemigrations hr --empty --name create_qas105_departments
```

Edit migration:

```python
from django.db import migrations

def create_departments(apps, schema_editor):
    Department = apps.get_model('hr', 'Department')

    departments = [
        # Top Level
        {'code': 'GM', 'name': 'General Management', 'parent': None},

        # Main Departments
        {'code': 'TECH', 'name': 'Technology (Engineering)', 'parent': None},
        {'code': 'SALES', 'name': 'Sales & Field Operations', 'parent': None},
        {'code': 'SUPPLY', 'name': 'Supply Chain & Logistics', 'parent': None},
        {'code': 'OPS', 'name': 'Operations / Manufacturing', 'parent': None},
        {'code': 'QA', 'name': 'Quality Assurance/Quality Control', 'parent': None},
        {'code': 'HSSE', 'name': 'Health, Safety, Security & Environment', 'parent': None},
        {'code': 'HR', 'name': 'Human Resources & Administration', 'parent': None},
        {'code': 'FIN', 'name': 'Finance & Accounting', 'parent': None},
        {'code': 'IT_ERP', 'name': 'IT & ERP Systems', 'parent': None},
    ]

    # Create parent departments first
    dept_objects = {}
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults={
                'name': dept_data['name'],
                'is_active': True
            }
        )
        dept_objects[dept_data['code']] = dept

    # Create sub-departments
    sub_departments = [
        {'code': 'FC_REPAIR', 'name': 'FC Repair & Refurbishment', 'parent': 'OPS'},
        {'code': 'NEW_BIT', 'name': 'New Bit Manufacturing', 'parent': 'OPS'},
        {'code': 'MAINT', 'name': 'Maintenance', 'parent': 'OPS'},
    ]

    for sub_dept_data in sub_departments:
        parent = dept_objects.get(sub_dept_data['parent'])
        Department.objects.get_or_create(
            code=sub_dept_data['code'],
            defaults={
                'name': sub_dept_data['name'],
                'parent': parent,
                'is_active': True
            }
        )

def reverse_departments(apps, schema_editor):
    Department = apps.get_model('hr', 'Department')
    codes = [
        'GM', 'TECH', 'SALES', 'SUPPLY', 'OPS', 'QA', 'HSSE',
        'HR', 'FIN', 'IT_ERP', 'FC_REPAIR', 'NEW_BIT', 'MAINT'
    ]
    Department.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('hr', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunPython(create_departments, reverse_departments),
    ]
```

---

### 2.2 Create Position Records

**⚠️ Follow ForeignKey patterns from ERRORS_FIXED_AND_PREVENTION.md**

#### Step 1: Review Position Model

```python
class Position(models.Model):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,  # ⚠️ Use PROTECT
        related_name='positions'  # ⚠️ Always add related_name
    )
    grade_level = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('EXEC', 'Executive'),
            ('MGR', 'Manager'),
            ('SUPV', 'Supervisor'),
            ('COORD', 'Coordinator'),
            ('ENG', 'Engineer'),
            ('TECH', 'Technician'),
            ('STAFF', 'Staff'),
        ]
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # ⚠️ Use timezone.now
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Step 2: Create Position Data Migration

```python
# Create data migration
python manage.py makemigrations hr --empty --name create_qas105_positions
```

Edit migration:

```python
from django.db import migrations

def create_positions(apps, schema_editor):
    Department = apps.get_model('hr', 'Department')
    Position = apps.get_model('hr', 'Position')

    # Get departments
    tech = Department.objects.get(code='TECH')
    sales = Department.objects.get(code='SALES')
    supply = Department.objects.get(code='SUPPLY')
    ops = Department.objects.get(code='OPS')
    fc_repair = Department.objects.get(code='FC_REPAIR')
    qa = Department.objects.get(code='QA')
    hsse = Department.objects.get(code='HSSE')
    hr_dept = Department.objects.get(code='HR')
    fin = Department.objects.get(code='FIN')
    it_erp = Department.objects.get(code='IT_ERP')

    positions = [
        # General Management
        {'code': 'GM', 'title': 'General Manager (GM)', 'dept': Department.objects.get(code='GM'), 'grade': 'EXEC'},

        # Technology / Engineering
        {'code': 'TECH_MGR', 'title': 'Technology Manager (TM)', 'dept': tech, 'grade': 'MGR'},
        {'code': 'ADE', 'title': 'Application Design Engineer (ADE)', 'dept': tech, 'grade': 'ENG'},
        {'code': 'AE', 'title': 'Application Engineer (AE)', 'dept': tech, 'grade': 'ENG'},
        {'code': 'PE', 'title': 'Product Engineer (PE)', 'dept': tech, 'grade': 'ENG'},
        {'code': 'ME', 'title': 'Manufacturing Engineer (ME)', 'dept': tech, 'grade': 'ENG'},

        # Sales & Field Operations
        {'code': 'SALES_MGR', 'title': 'Sales Manager', 'dept': sales, 'grade': 'MGR'},
        {'code': 'FSE', 'title': 'Field Service Engineer (FSE)', 'dept': sales, 'grade': 'ENG'},
        {'code': 'SALES_REP', 'title': 'Sales Representative', 'dept': sales, 'grade': 'STAFF'},

        # Supply Chain & Logistics
        {'code': 'SUPPLY_MGR', 'title': 'Supply Chain Manager', 'dept': supply, 'grade': 'MGR'},
        {'code': 'BUYER', 'title': 'Buyer / Purchasing Agent', 'dept': supply, 'grade': 'STAFF'},
        {'code': 'INV_CTRL', 'title': 'Inventory Controller', 'dept': supply, 'grade': 'STAFF'},

        # Operations / Manufacturing
        {'code': 'OPS_MGR', 'title': 'Operations Manager', 'dept': ops, 'grade': 'MGR'},
        {'code': 'PROD_SUPV', 'title': 'Production Supervisor', 'dept': ops, 'grade': 'SUPV'},

        # FC Repair & Refurbishment (Sub-department of Operations)
        {'code': 'FC_REFURB_SUPV', 'title': 'FC Refurbish Supervisor', 'dept': fc_repair, 'grade': 'SUPV',
         'desc': 'Current title for FC repair and new bit production supervision. Functionally equivalent to Repair Coordinator role.'},
        {'code': 'REPAIR_COORD', 'title': 'Repair Coordinator', 'dept': fc_repair, 'grade': 'COORD',
         'desc': 'From QAS-105. May be legacy position, now called FC Refurbish Supervisor.'},
        {'code': 'REPAIR_SUPV', 'title': 'Repair Supervisor', 'dept': fc_repair, 'grade': 'SUPV'},
        {'code': 'REPAIR_TECH', 'title': 'Repair Technician', 'dept': fc_repair, 'grade': 'TECH'},

        # Quality
        {'code': 'QA_MGR', 'title': 'Quality Assurance Manager', 'dept': qa, 'grade': 'MGR'},
        {'code': 'QA_COORD', 'title': 'QA/QC Coordinator', 'dept': qa, 'grade': 'COORD'},
        {'code': 'QC_INSP', 'title': 'QC Inspector', 'dept': qa, 'grade': 'TECH'},

        # HSSE
        {'code': 'HSE_MGR', 'title': 'HSE Manager', 'dept': hsse, 'grade': 'MGR'},
        {'code': 'SAFETY_COORD', 'title': 'Safety Coordinator', 'dept': hsse, 'grade': 'COORD'},

        # HR
        {'code': 'HR_MGR', 'title': 'HR Manager', 'dept': hr_dept, 'grade': 'MGR'},
        {'code': 'HR_COORD', 'title': 'HR Coordinator', 'dept': hr_dept, 'grade': 'COORD'},

        # Finance
        {'code': 'FIN_CTRL', 'title': 'Financial Controller', 'dept': fin, 'grade': 'MGR'},
        {'code': 'ACCOUNTANT', 'title': 'Accountant', 'dept': fin, 'grade': 'STAFF'},

        # IT & ERP
        {'code': 'IT_MGR', 'title': 'IT/ERP Manager', 'dept': it_erp, 'grade': 'MGR'},
        {'code': 'SYS_ADMIN', 'title': 'System Administrator', 'dept': it_erp, 'grade': 'STAFF'},
        {'code': 'ERP_ADMIN', 'title': 'ERP Administrator', 'dept': it_erp, 'grade': 'STAFF'},
    ]

    for pos_data in positions:
        Position.objects.get_or_create(
            code=pos_data['code'],
            defaults={
                'title': pos_data['title'],
                'department': pos_data['dept'],
                'grade_level': pos_data['grade'],
                'description': pos_data.get('desc', ''),
                'is_active': True
            }
        )

def reverse_positions(apps, schema_editor):
    Position = apps.get_model('hr', 'Position')
    Position.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('hr', 'XXXX_create_qas105_departments'),
    ]

    operations = [
        migrations.RunPython(create_positions, reverse_positions),
    ]
```

---

### 2.3 Link Employees to Positions and Departments

**⚠️ Follow relationship patterns from ERRORS_FIXED_AND_PREVENTION.md Section 2**

#### Step 1: Review Employee/HRPeople Model

```python
class HRPeople(models.Model):  # or Employee
    # ... personal fields ...

    # ⚠️ Ensure proper ForeignKey with related_name
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'  # ⚠️ Always add related_name
    )

    # Option 1: Derive department from position
    @property
    def department(self):
        return self.position.department if self.position else None

    # Option 2: Keep explicit department FK (if already exists)
    # department = models.ForeignKey(
    #     Department,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name='employees'
    # )
```

#### Step 2: Add Signal to Keep Department in Sync (if using explicit department FK)

**⚠️ Follow signal patterns from ERRORS_FIXED_AND_PREVENTION.md Section 7**

```python
# floor_app/operations/hr/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import HRPeople

@receiver(pre_save, sender=HRPeople)
def sync_department_from_position(sender, instance, **kwargs):
    """
    Automatically sync department from position when position changes.
    ⚠️ Guard against infinite loops.
    """
    if instance.position:
        instance.department = instance.position.department
```

Register signals in apps.py:

```python
# floor_app/operations/hr/apps.py

class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.hr'

    def ready(self):
        import floor_app.operations.hr.signals  # ⚠️ Import signals here
```

---

## PART 3: Deliverables

### 3.1 Create Documentation

Create: `docs/refactor_ownership_and_org_structure.md`

**Template:**

```markdown
# Model Ownership and Organization Structure Refactoring

## Date: YYYY-MM-DD

## Summary

This refactoring fixed model ownership issues and established proper organizational structure based on QAS-105.

---

## 1. Model Ownership Changes

### 1.1 Engineering App Created

**Models moved from Inventory to Engineering:**

| Model | Old Location | New Location | Database Table |
|-------|--------------|--------------|----------------|
| BitDesign | inventory.models | engineering.models | inventory_bitdesign |
| BitDesignRevision | inventory.models | engineering.models | inventory_bitdesignrevision |
| BOMHeader | inventory.models | engineering.models | inventory_bomheader |
| BOMLine | inventory.models | engineering.models | inventory_bomline |
| RollerConeDesign | inventory.models | engineering.models | inventory_rollerconedesign |
| RollerConeBOM | inventory.models | engineering.models | inventory_rollerconebom |

**Rationale:**
- Engineering owns design and BOM definitions (what is needed to build/repair)
- Inventory owns stock, locations, movements (physical items)
- Clear separation of concerns

**Files Updated:**
- Created: `floor_app/operations/engineering/` (complete app structure)
- Modified: `floor_app/operations/inventory/models/__init__.py` (removed exports)
- Modified: [list all files with updated imports]
- Modified: [list all admin, form, view, template files]

### 1.2 Production Ownership Verified

**Confirmed these models belong to Production:**
- JobCard
- OperationDefinition
- [list others if applicable]

**No changes needed** - ownership is correct.

### 1.3 Financial Fields Removed from Quality NCR

**Changes to NonconformanceReport model:**

Removed fields:
- `estimated_cost_impact`
- `actual_cost_impact`
- `lost_revenue`

**Created NCRFinancialImpact model:**
- Location: `floor_app/operations/finance/models/ncr_financial.py`
- Database table: `finance_ncr_financial_impact`
- Relationship: OneToOne with NCR

**Rationale:**
- Separation of duties: QA logs quality issues, Finance tracks costs
- QA users no longer required to enter financial data
- Finance has full control over cost impact calculations

**Data Migration:**
- Migration file: `quality/migrations/XXXX_migrate_financial_fields_to_finance.py`
- All existing financial data successfully migrated
- No data loss

**Files Updated:**
- Modified: `floor_app/operations/quality/models.py` (removed financial fields)
- Modified: `floor_app/operations/quality/forms.py` (removed financial fields)
- Modified: `floor_app/operations/quality/admin.py` (removed financial columns)
- Created: `floor_app/operations/finance/models/ncr_financial.py`
- Created: `floor_app/operations/finance/admin.py`

---

## 2. Organization Structure

### 2.1 Departments Created

**Top-level departments (from QAS-105):**

| Code | Name | Parent | Description |
|------|------|--------|-------------|
| GM | General Management | - | Executive leadership |
| TECH | Technology (Engineering) | - | Design, R&D, product engineering |
| SALES | Sales & Field Operations | - | Sales, field service |
| SUPPLY | Supply Chain & Logistics | - | Purchasing, inventory control |
| OPS | Operations / Manufacturing | - | Production, repair, maintenance |
| QA | Quality Assurance/QC | - | Quality control and assurance |
| HSSE | Health, Safety, Security, Environment | - | Safety and compliance |
| HR | Human Resources & Administration | - | HR, admin |
| FIN | Finance & Accounting | - | Finance, accounting |
| IT_ERP | IT & ERP Systems | - | IT infrastructure, ERP |

**Sub-departments:**

| Code | Name | Parent | Description |
|------|------|--------|-------------|
| FC_REPAIR | FC Repair & Refurbishment | OPS | FC bit repair operations |
| NEW_BIT | New Bit Manufacturing | OPS | New bit production |
| MAINT | Maintenance | OPS | Equipment maintenance |

**Total departments created:** 13

**Migration file:** `hr/migrations/XXXX_create_qas105_departments.py`

### 2.2 Positions Created

**Summary by department:**

| Department | Positions Created | Key Positions |
|------------|-------------------|---------------|
| GM | 1 | General Manager |
| Technology | 5 | Technology Manager, ADE, AE, PE, ME |
| Sales | 3 | Sales Manager, FSE, Sales Rep |
| Supply Chain | 3 | Supply Chain Manager, Buyer, Inventory Controller |
| Operations | 2 | Operations Manager, Production Supervisor |
| FC Repair | 4 | FC Refurbish Supervisor, Repair Coordinator, Repair Supervisor, Repair Technician |
| Quality | 3 | QA Manager, QA Coordinator, QC Inspector |
| HSSE | 2 | HSE Manager, Safety Coordinator |
| HR | 2 | HR Manager, HR Coordinator |
| Finance | 2 | Financial Controller, Accountant |
| IT/ERP | 3 | IT/ERP Manager, System Admin, ERP Admin |

**Total positions created:** 30

**Special note on FC Refurbish Supervisor:**
- Code: `FC_REFURB_SUPV`
- Title: "FC Refurbish Supervisor"
- This is the current real-world title used
- Functionally equivalent to "Repair Coordinator" from QAS-105
- Oversees FC repair operations and new bit production supervision
- Both positions retained for historical tracking

**Migration file:** `hr/migrations/XXXX_create_qas105_positions.py`

### 2.3 Employee-Position Linking

**Changes to HRPeople/Employee model:**
- [Describe any schema changes]
- [Describe how department is derived/synced from position]

**Signal added:**
- `sync_department_from_position` - automatically updates employee department when position changes

---

## 3. Migrations Summary

**All migrations applied successfully:**

```bash
python manage.py showmigrations

engineering
 [X] 0001_initial

quality
 [X] XXXX_migrate_financial_fields_to_finance
 [X] XXXX_remove_financial_fields_from_ncr

finance
 [X] 0001_initial
 [X] 0002_ncr_financial_impact

hr
 [X] XXXX_create_qas105_departments
 [X] XXXX_create_qas105_positions
```

**Data integrity verified:**
- All design/BOM data intact after move
- All financial data migrated successfully
- No orphaned records

---

## 4. Testing Performed

- [X] `python manage.py check` - No errors
- [X] All migrations applied without errors
- [X] Admin interfaces tested for moved models
- [X] Forms tested for NCR (no financial fields visible)
- [X] Finance admin shows NCRFinancialImpact correctly
- [X] Department and Position data visible in admin
- [X] No import errors in application startup

---

## 5. Breaking Changes

**For developers:**

1. **Import paths changed** for design/BOM models:
   ```python
   # Old
   from floor_app.operations.inventory.models import BitDesign, BOMHeader

   # New
   from floor_app.operations.engineering.models import BitDesign, BOMHeader
   ```

2. **NCR financial fields removed**:
   ```python
   # Old
   ncr.estimated_cost_impact

   # New
   ncr.financial_impact.total_impact  # Access via related model
   ```

3. **Template paths changed**:
   ```
   Old: floor_app/templates/inventory/bit_designs/
   New: floor_app/templates/engineering/bit_designs/
   ```

**For users:**

1. **QA users** no longer see or enter financial data in NCR forms
2. **Finance users** now access financial impact via Finance module
3. **Organization structure** now reflects official QAS-105 job titles

---

## 6. Future Recommendations

1. **Add permissions** to restrict Finance module access
2. **Create Finance dashboard** for cost impact analytics
3. **Update reports** to use new organization structure
4. **Train users** on new QAS-105 position titles
5. **Review employee position assignments** and update as needed

---

## 7. References

- `ERRORS_FIXED_AND_PREVENTION.md` - Error prevention guidelines followed
- `fms_structure_overview.md` - System architecture analysis
- `model_ownership_mapping.csv` - Ownership analysis
- QAS-105 Job Titles Document - Official ARDT organization structure
```

---

### 3.2 Final Verification

**Run these commands and include output in documentation:**

```bash
# Check for errors
python manage.py check

# Verify migrations
python manage.py showmigrations

# Count departments and positions
python manage.py shell
>>> from floor_app.operations.hr.models import Department, Position
>>> Department.objects.count()
>>> Position.objects.count()
>>> exit()

# Test server starts
python manage.py runserver --noreload
```

---

## CRITICAL REMINDERS

**⚠️ Before committing, verify:**

- [ ] Read `ERRORS_FIXED_AND_PREVENTION.md` Section "Before Every Commit"
- [ ] Run `python manage.py check` - no errors
- [ ] Run `python manage.py makemigrations --dry-run` - no unexpected migrations
- [ ] All imports use absolute paths, not relative
- [ ] All ForeignKeys have `related_name`
- [ ] All ForeignKeys use appropriate `on_delete` (PROTECT for business data)
- [ ] All datetime fields use `timezone.now`, not `datetime.now`
- [ ] All admin classes updated for moved models
- [ ] All forms updated for moved models
- [ ] All templates updated for moved models
- [ ] Migrations tested and applied
- [ ] Documentation complete
- [ ] Server starts without errors

**⚠️ Common mistakes to avoid (from ERRORS_FIXED_AND_PREVENTION.md):**
- ❌ Circular imports
- ❌ Missing related_name
- ❌ Forms referencing non-existent fields
- ❌ Admin list_display with non-existent fields
- ❌ Forgetting to update imports after moving models
- ❌ Using datetime.now() instead of timezone.now()
- ❌ Not running migrations
- ❌ Not testing admin interface

---

## SUCCESS CRITERIA

This task is complete when:

1. ✅ Engineering app created with all design/BOM models moved
2. ✅ Financial fields removed from NCR and moved to Finance
3. ✅ All departments from QAS-105 created
4. ✅ All positions from QAS-105 created
5. ✅ Employee-position linking verified
6. ✅ All migrations applied successfully
7. ✅ `python manage.py check` passes with no errors
8. ✅ Server starts without errors
9. ✅ Documentation created in `docs/refactor_ownership_and_org_structure.md`
10. ✅ All changes committed to `feat/ownership-and-org-structure` branch

**Review the error prevention guide throughout the task. Follow the patterns. Test frequently.**

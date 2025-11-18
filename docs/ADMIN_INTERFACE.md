# Admin Interface Documentation

## Overview
This document provides a comprehensive overview of Django admin registrations across the Floor Management System.

## Admin Structure

### Core App (`core/admin.py`)
All core business models are registered here:

#### Registered Models:
1. **UserPreference** - User interface preferences
   - List display: user, theme, font_size, table_density, updated_at
   - Filters: theme, font_size, table_density
   - Search: username, email

2. **CostCenter** - Organizational cost centers
   - List display: code, name, parent, manager, status, annual_budget, currency
   - Filters: status, currency
   - Search: code, name, description, erp_cost_center_code
   - Autocomplete: parent, manager

3. **ERPDocumentType** - ERP document type definitions
   - List display: code, name, erp_system, is_active
   - Filters: is_active, erp_system
   - Search: code, name, description

4. **ERPReference** - ERP system references
   - List display: document_type, erp_number, erp_line_number, content_type, object_id, sync_status, created_at
   - Filters: document_type, sync_status, content_type
   - Search: erp_number, notes
   - Date hierarchy: created_at

5. **LossOfSaleCause** - Loss of sale cause categories
   - List display: code, name, category, is_active
   - Filters: category, is_active
   - Search: code, name, description

6. **LossOfSaleEvent** - Loss of sale event tracking
   - List display: reference_number, title, cause, event_date, estimated_loss_amount, currency, status, reported_by
   - Filters: status, cause__category, cause, cost_center
   - Search: reference_number, title, description, customer, order
   - Date hierarchy: event_date
   - Autocomplete: cause, cost_center, users

7. **ApprovalType** - Approval workflow types
   - List display: code, name, is_active
   - Filters: is_active
   - Search: code, name, description

8. **ApprovalAuthority** - Approval authority definitions
   - List display: approval_type, user, group, position_id, min_amount, max_amount, priority, is_active
   - Filters: approval_type, is_active
   - Search: username, group name

9. **Currency** - Currency definitions
   - List display: code, name, symbol, decimal_places, is_base_currency, is_active
   - Filters: is_active, is_base_currency
   - Search: code, name

10. **ExchangeRate** - Currency exchange rates
    - List display: from_currency, to_currency, rate, effective_date
    - Filters: from_currency, to_currency
    - Date hierarchy: effective_date

---

### HR App (`floor_app/admin.py`)
All HR models are centralized in the main floor_app/admin.py to prevent duplicate registrations:

#### Registered Models:
1. **HRPeople** - Person master data
   - List display: id, full_name_en, gender, nationality, national_id, iqama_number
   - Filters: gender, nationality
   - Search: names (EN/AR), national_id, iqama_number
   - Inlines: HRPhone, HREmail, Address
   - Fieldsets: Names (EN/AR), Personal Info, Nationality & ID, Identity Verification, Photo, System Info

2. **HRPhone** - Person phone numbers
   - List display: phone_e164, country_iso2, kind, use, person
   - Filters: kind, use, country_iso2
   - Search: phone_e164
   - Autocomplete: person

3. **HREmail** - Person email addresses
   - List display: email, kind, is_verified, person
   - Filters: kind, is_verified
   - Search: email
   - Autocomplete: person

4. **HREmployee** - Employee records
   - List display: employee_no, person, position, department, status, contract_type
   - Filters: status, contract_type, department, employment_status
   - Search: employee_no, person names (EN/AR)
   - Autocomplete: person, user, position, department, supervisor
   - Fieldsets: Person & User, Employee Details, Job Assignment, Contract Info, Probation, Employment Dates, Work Schedule, Compensation, Reporting, Supervision, System Info
   - Custom templates: change_form.html, change_list.html

5. **Position** - Job positions
   - List display: name, department, position_level, salary_grade, employee_count, is_active
   - Filters: department, position_level, salary_grade, is_active
   - Search: name, description
   - Autocomplete: department

6. **Department** - Organizational departments
   - List display: name, code, department_type, cost_center, head_count
   - Filters: department_type, is_active
   - Search: name, code, description
   - Autocomplete: parent_department, cost_center

7. **HRQualification** - Qualification definitions
   - List display: code, name, level, issuer_type, validity_months, requires_renewal, is_active
   - Filters: issuer_type, requires_renewal, is_active
   - Search: code, name

8. **HREmployeeQualification** - Employee qualification assignments
   - List display: employee, qualification, issued_at, expires_at, status
   - Filters: status, qualification
   - Search: employee__person names, qualification name
   - Autocomplete: employee, qualification

9. **Address** - Generic address model (via ContentType)
   - List display: address_line1, city, state, country, postal_code, address_type
   - Filters: country, address_type
   - Search: address lines, city, state

---

### Inventory App (`floor_app/operations/inventory/admin/`)
Modular admin structure with separate files for different model groups:

#### Structure:
- `__init__.py` - Imports all admin modules
- `reference.py` - Reference data (ConditionType, OwnershipType, UnitOfMeasure, ItemCategory)
- `bit_design.py` - Bit design models
- `item.py` - Item master
- `stock.py` - Location and stock models
- `bom.py` - Bill of Materials
- `transactions.py` - Inventory transactions

#### Reference Data (`reference.py`):
1. **ConditionType** - Item condition types
2. **OwnershipType** - Ownership categories
3. **UnitOfMeasure** - Units of measurement
4. **ItemCategory** - Item categorization

#### Bit Design (`bit_design.py`):
1. **BitDesignLevel** - Design levels (L3, L4, L5)
   - List display: code, name, sort_order, is_active
   - Filters: is_active
   - Ordering: sort_order, code

2. **BitDesignType** - Design type categories
   - List display: code, name, sort_order, is_active
   - Filters: is_active
   - Ordering: sort_order, code

3. **BitDesign** - Bit design master
   - List display: design_code, name, level, size_inches, connection_type, blade_count, created_at
   - Filters: level, is_deleted
   - Search: design_code, name, connection_type
   - Inlines: BitDesignRevision
   - Fieldsets: Identification, Design Specifications, Details, Audit

4. **BitDesignRevision** - MAT revisions
   - List display: mat_number, bit_design, revision_code, design_type, is_temporary, is_active, effective_date
   - Filters: is_active, is_temporary, design_type, level
   - Search: mat_number, design_code
   - Raw ID fields: bit_design, superseded_by
   - Fieldsets: MAT Identification, Status, Change Information, Audit

#### Item Master (`item.py`):
1. **Item** - Item master records
   - Comprehensive display with SKU, name, category, UOM, stock levels
   - Advanced filtering and search
   - Fieldsets for organization

#### Stock (`stock.py`):
1. **Location** - Inventory locations
   - Hierarchical location structure
   - GPS coordinates support

2. **SerialUnit** - Serialized inventory units
   - Serial number tracking
   - Status management
   - MAT tracking

3. **InventoryStock** - Non-serialized stock
   - Quantity tracking
   - Reorder point monitoring

#### BOM (`bom.py`):
1. **BOMHeader** - Bill of Materials header
2. **BOMLine** - BOM line items

#### Transactions (`transactions.py`):
1. **InventoryTransaction** - All inventory movements

---

## Admin Features Used

### Common Features Across Models:
1. **List Display** - Customized column display in list views
2. **List Filters** - Right sidebar filtering
3. **Search Fields** - Full-text search capability
4. **Ordering** - Default sort order
5. **Readonly Fields** - System fields protected from editing
6. **Autocomplete Fields** - AJAX-powered foreign key selects
7. **Date Hierarchy** - Date-based drilling
8. **Fieldsets** - Organized form sections
9. **Inlines** - Related model editing
10. **Raw ID Fields** - Performance optimization for large datasets
11. **Custom Templates** - Specialized admin interfaces

### Advanced Features:
1. **Collapsible Fieldsets** - Audit info hidden by default
2. **TabularInline** - Compact inline editing
3. **Show Change Link** - Direct navigation from inlines
4. **Custom Querysets** - Optimized with select_related/prefetch_related
5. **Computed Display Fields** - Methods for calculated columns

---

## Best Practices Followed

### 1. **Modular Organization**
- Core models in `core/admin.py`
- HR models centralized in `floor_app/admin.py`
- Inventory uses modular `admin/` directory structure
- Prevents duplicate registration errors

### 2. **Performance Optimization**
- `select_related()` for foreign keys
- `prefetch_related()` for reverse relations
- `raw_id_fields` for large datasets
- `autocomplete_fields` for better UX

### 3. **User Experience**
- Logical fieldset groupings
- Collapsed audit sections
- Inline editing for related models
- Comprehensive search and filters
- Date hierarchies for temporal data

### 4. **Audit Trail**
- Readonly timestamp fields
- Created/updated by tracking
- System info in collapsed fieldsets

### 5. **Data Integrity**
- Autocomplete prevents invalid selections
- Required vs optional fields clearly marked
- Validation at admin level

---

## Adding New Admin Registrations

### For Core Models:
Add to `core/admin.py`:
```python
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['field1', 'field2']
    list_filter = ['field3']
    search_fields = ['field1', 'field4']
```

### For HR Models:
Add to `floor_app/admin.py`:
```python
from .operations.hr.models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    # ... configuration
```

### For Inventory Models:
Create/update file in `floor_app/operations/inventory/admin/`:
1. Create new file (e.g., `your_module.py`)
2. Register models
3. Import in `admin/__init__.py`

---

## Custom Admin Templates

### HR Employee Admin:
- **Change Form**: `admin/floor_app/hremployee/change_form.html`
- **Change List**: `admin/floor_app/hremployee/change_list.html`

These templates provide enhanced UI for employee management with quick actions and custom layouts.

---

## Quick Reference

### Most Common Admin Options:
```python
@admin.register(ModelName)
class ModelNameAdmin(admin.ModelAdmin):
    # Display
    list_display = ['field1', 'field2']           # Columns in list view
    list_filter = ['field3', 'field4']            # Right sidebar filters
    search_fields = ['field1', 'field5']          # Search box fields
    ordering = ['-created_at']                    # Default sort
    date_hierarchy = 'created_at'                 # Date drill-down

    # Form
    fieldsets = (...)                             # Organized form sections
    readonly_fields = ['created_at', 'updated_at'] # Protected fields
    autocomplete_fields = ['fk_field']            # AJAX dropdowns
    raw_id_fields = ['large_fk_field']            # Performance opt

    # Related
    inlines = [RelatedModelInline]                # Edit related inline

    # Performance
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fk_field')
```

---

## Maintenance Notes

### Regular Tasks:
1. **Review Search Fields** - Ensure commonly searched fields are indexed
2. **Optimize Queries** - Add select_related/prefetch_related as needed
3. **Update Filters** - Add filters for new categorical fields
4. **Test Autocomplete** - Verify performance with large datasets
5. **Review Permissions** - Ensure proper access controls

### When Adding Models:
1. Register in appropriate admin file
2. Configure list_display with key fields
3. Add relevant filters and search
4. Include readonly audit fields
5. Test with sample data
6. Document in this file

---

Last Updated: 2025-11-18

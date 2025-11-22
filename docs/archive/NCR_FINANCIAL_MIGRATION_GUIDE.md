# NCR Financial Data Migration Guide

## Overview

This guide explains the data migration process for separating financial fields from the Quality NCR model into the new Finance app.

**Status:** Finance app created, awaiting data migration and field removal
**Created:** 2025-11-21
**Part of:** Model Ownership Refactoring - Part 1.3

---

## What Changed

### Fields Being Migrated

Three financial fields are being moved from `quality.NonconformanceReport` to `finance.NCRFinancialImpact`:

1. **estimated_cost_impact** (DecimalField)
   - Description: Estimated cost of the nonconformance
   - Type: DecimalField(max_digits=12, decimal_places=2, default=0)

2. **actual_cost_impact** (DecimalField)
   - Description: Actual cost after resolution
   - Type: DecimalField(max_digits=12, decimal_places=2, default=0)

3. **lost_revenue** (DecimalField)
   - Description: Lost revenue due to this NCR
   - Type: DecimalField(max_digits=12, decimal_places=2, default=0)

### Rationale

**Domain Separation:**
- Quality app owns process/compliance data (what went wrong, how to fix it)
- Finance app owns cost/impact data (how much it costs)
- Maintains clear boundaries between operational and financial concerns

**Benefits:**
- Cleaner domain models
- Separate access control for financial data
- Independent financial reporting without quality module dependencies
- Follows single responsibility principle

---

## Migration Steps

### Phase 1: Create Finance App ✅ COMPLETE

- [x] Created `floor_app/operations/finance/` app structure
- [x] Created `NCRFinancialImpact` model
- [x] Created admin interface for financial data
- [x] Added Finance app to `INSTALLED_APPS`

### Phase 2: Generate Initial Migrations (PENDING - Requires Python Environment)

**Run these commands once Python venv is available:**

```bash
# Generate migration for new Finance app
python manage.py makemigrations finance

# Generate migration for Quality app (will detect field removal later)
# Don't run this yet - wait until after data migration
```

### Phase 3: Create Data Migration (PENDING)

Create a data migration to copy existing financial data from NCR to NCRFinancialImpact:

```bash
# Create empty data migration
python manage.py makemigrations finance --empty --name migrate_ncr_financial_data
```

**Edit the migration file** (`finance/migrations/XXXX_migrate_ncr_financial_data.py`):

```python
from django.db import migrations


def migrate_ncr_financial_data(apps, schema_editor):
    """
    Copy financial data from NonconformanceReport to NCRFinancialImpact.
    """
    NonconformanceReport = apps.get_model('quality', 'NonconformanceReport')
    NCRFinancialImpact = apps.get_model('finance', 'NCRFinancialImpact')

    # Get all NCRs with financial data
    ncrs_with_financial_data = NonconformanceReport.objects.filter(
        models.Q(estimated_cost_impact__gt=0) |
        models.Q(actual_cost_impact__gt=0) |
        models.Q(lost_revenue__gt=0)
    )

    # Create NCRFinancialImpact records
    financial_impacts = []
    for ncr in ncrs_with_financial_data:
        financial_impacts.append(
            NCRFinancialImpact(
                ncr_number=ncr.ncr_number,
                estimated_cost_impact=ncr.estimated_cost_impact,
                actual_cost_impact=ncr.actual_cost_impact,
                lost_revenue=ncr.lost_revenue,
                created_at=ncr.created_at,
                updated_at=ncr.updated_at,
                created_by=ncr.created_by,
                updated_by=ncr.updated_by,
            )
        )

    # Bulk create for efficiency
    if financial_impacts:
        NCRFinancialImpact.objects.bulk_create(financial_impacts)
        print(f"Migrated financial data for {len(financial_impacts)} NCRs")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration: copy data back from NCRFinancialImpact to NCR.
    """
    NonconformanceReport = apps.get_model('quality', 'NonconformanceReport')
    NCRFinancialImpact = apps.get_model('finance', 'NCRFinancialImpact')

    for impact in NCRFinancialImpact.objects.all():
        try:
            ncr = NonconformanceReport.objects.get(ncr_number=impact.ncr_number)
            ncr.estimated_cost_impact = impact.estimated_cost_impact
            ncr.actual_cost_impact = impact.actual_cost_impact
            ncr.lost_revenue = impact.lost_revenue
            ncr.save(update_fields=[
                'estimated_cost_impact',
                'actual_cost_impact',
                'lost_revenue'
            ])
        except NonconformanceReport.DoesNotExist:
            print(f"Warning: NCR {impact.ncr_number} not found during rollback")


class Migration(migrations.Migration):
    dependencies = [
        ('finance', '0001_initial'),
        ('quality', '0001_initial'),  # Adjust to actual quality migration number
    ]

    operations = [
        migrations.RunPython(
            migrate_ncr_financial_data,
            reverse_migration
        ),
    ]
```

### Phase 4: Apply Data Migration (PENDING)

```bash
# Run the data migration
python manage.py migrate finance

# Verify data was copied correctly
python manage.py shell
>>> from floor_app.operations.quality.models import NonconformanceReport
>>> from floor_app.operations.finance.models import NCRFinancialImpact
>>> ncr_count = NonconformanceReport.objects.filter(
...     estimated_cost_impact__gt=0
... ).count()
>>> impact_count = NCRFinancialImpact.objects.count()
>>> print(f"NCRs with financial data: {ncr_count}")
>>> print(f"Financial impact records: {impact_count}")
>>> # Should match or impact_count should be >= ncr_count
```

### Phase 5: Remove Fields from NCR Model (PENDING)

**Once data migration is verified:**

1. Edit `floor_app/operations/quality/models/ncr.py`
2. Remove these fields from `NonconformanceReport` model:
   - `estimated_cost_impact`
   - `actual_cost_impact`
   - `lost_revenue`

3. Add a helper method for accessing financial data:

```python
# Add to NonconformanceReport model
@property
def financial_impact(self):
    """Get associated financial impact data."""
    try:
        from floor_app.operations.finance.models import NCRFinancialImpact
        return NCRFinancialImpact.objects.get(ncr_number=self.ncr_number)
    except NCRFinancialImpact.DoesNotExist:
        return None
```

4. Generate migration for field removal:

```bash
python manage.py makemigrations quality
# Will create migration to remove the three fields
```

### Phase 6: Update Forms and Admin (PENDING)

**Update NCR Forms:**

Edit `floor_app/operations/quality/forms.py`:
- Remove financial fields from NCR form
- Create separate form for financial data if needed

**Update NCR Admin:**

Edit `floor_app/operations/quality/admin.py`:
- Remove financial fields from list_display
- Remove financial fields from fieldsets
- Optionally add inline for financial impact
- Update filters if they reference financial fields

**Example inline:**

```python
from floor_app.operations.finance.models import NCRFinancialImpact

class NCRFinancialImpactInline(admin.StackedInline):
    model = NCRFinancialImpact
    extra = 0
    fields = ['estimated_cost_impact', 'actual_cost_impact', 'lost_revenue', 'notes']

# Add to NonconformanceReportAdmin
inlines = [NCRFinancialImpactInline]
```

### Phase 7: Apply Final Migration (PENDING)

```bash
# Apply the field removal migration
python manage.py migrate quality

# Run Django check to ensure no errors
python manage.py check

# Test admin interface
python manage.py runserver
# Navigate to admin and test NCR CRUD operations
```

---

## Verification Checklist

Before marking migration complete:

- [ ] Finance app migrations created and applied
- [ ] Data migration executed successfully
- [ ] All NCR financial data copied to NCRFinancialImpact
- [ ] NCR model fields removed
- [ ] Quality app migrations applied
- [ ] Forms updated
- [ ] Admin interface updated
- [ ] No Django errors from `python manage.py check`
- [ ] Admin interface tested for NCR CRUD
- [ ] Financial data accessible via finance app
- [ ] No broken references in codebase

---

## Rollback Procedure

If issues are encountered:

1. Reverse the quality migration (restores fields):
   ```bash
   python manage.py migrate quality XXXX  # Previous migration number
   ```

2. Run reverse data migration if needed:
   ```bash
   python manage.py migrate finance XXXX  # Before data migration
   ```

3. Remove Finance app from INSTALLED_APPS if necessary

---

## Current Status

**Completed:**
- ✅ Finance app structure created
- ✅ NCRFinancialImpact model defined
- ✅ Admin interface created
- ✅ Finance app added to INSTALLED_APPS

**Pending (Blocked on Python Environment):**
- ⏳ Generate migrations
- ⏳ Create and run data migration
- ⏳ Remove fields from NCR model
- ⏳ Update forms and admin
- ⏳ Verification testing

**Next Steps:**
1. Set up Python virtual environment
2. Run `python manage.py makemigrations finance`
3. Create data migration as described above
4. Follow phases 3-7 above

---

## Files Changed

**Created:**
- `floor_app/operations/finance/__init__.py`
- `floor_app/operations/finance/apps.py`
- `floor_app/operations/finance/models/ncr_financial.py`
- `floor_app/operations/finance/models/__init__.py`
- `floor_app/operations/finance/admin/__init__.py`
- `floor_app/operations/finance/migrations/__init__.py`

**Modified:**
- `floor_mgmt/settings.py` - Added FinanceConfig to INSTALLED_APPS

**To be Modified (after migration):**
- `floor_app/operations/quality/models/ncr.py` - Remove 3 financial fields
- `floor_app/operations/quality/forms.py` - Update NCR forms
- `floor_app/operations/quality/admin.py` - Update admin interface

---

## Related Documentation

- Task File: `TASK_OWNERSHIP_AND_ORG_STRUCTURE.md`
- Progress: `PROGRESS_MODEL_OWNERSHIP.md`
- Error Guide: `ERRORS_FIXED_AND_PREVENTION.md`

---

**Last Updated:** 2025-11-21
**Status:** Finance app ready, awaiting Python environment for migration execution

# Field Duplication Analysis & Deduplication Plan

## Executive Summary

This document identifies redundant/duplicate fields across the FMS codebase that store the same or overlapping data. Having multiple fields with the same meaning leads to:
- **Data inconsistency** (fields get out of sync)
- **Confusion** (which field to use?)
- **Maintenance burden** (update logic in multiple places)
- **Database bloat** (unnecessary storage)

---

## ✅ CONFIRMED DUPLICATIONS

### 1. Inventory - Item Model (`floor_app/operations/inventory/models/item.py`)

**Problem: `min_stock_qty` is redundant**

#### Current Fields:
```python
min_stock_qty = models.DecimalField(...)  # ❌ REDUNDANT
reorder_point = models.DecimalField(...)  # ✅ KEEP - Used in business logic
reorder_qty = models.DecimalField(...)    # ✅ KEEP - How much to order
safety_stock = models.DecimalField(...)   # ✅ KEEP - Buffer quantity
lead_time_days = models.IntegerField(...) # ✅ KEEP - Procurement time
```

#### Analysis:
- **`reorder_point`**: Actively used in `core/services/planning_service.py` line 148
- **`min_stock_qty`**: Only displayed in admin, NOT used in any business logic
- **`safety_stock`**: Proper inventory management concept (buffer against variability)

In proper inventory management:
- **Reorder Point (ROP)** = (Average Daily Demand × Lead Time) + Safety Stock
- **Safety Stock** = Buffer to protect against demand/supply variability
- **Minimum Stock** is either:
  - Same as Safety Stock (minimum buffer), OR
  - Same as Reorder Point (when to order)

`min_stock_qty` is ambiguous and duplicates either `reorder_point` or `safety_stock`.

#### Recommendation:
```python
# REMOVE:
min_stock_qty = models.DecimalField(...)  # ❌ DELETE THIS FIELD

# KEEP (these are sufficient and correct):
reorder_point = models.DecimalField(...)  # When to order
reorder_qty = models.DecimalField(...)    # How much to order
safety_stock = models.DecimalField(...)   # Safety buffer
lead_time_days = models.IntegerField(...) # Lead time
```

#### Migration Plan:
1. **Data Migration**: Copy `min_stock_qty` → `reorder_point` if `reorder_point` is null/zero
2. **Remove Field**: Drop `min_stock_qty` column
3. **Update Admin**: Remove from fieldsets in `floor_app/operations/inventory/admin/item.py:35`
4. **Update Forms**: Remove from `floor_app/operations/inventory/forms.py`
5. **Update Templates**: Remove from `floor_app/operations/inventory/templates/inventory/items/form.html`

---

### 2. BitDesignRevision & BOMHeader - Cost Fields

**Problem: Overlapping cost fields between BitDesignRevision and BOMHeader**

#### Current State:

**BitDesignRevision (engineering/models/bit_design.py:273-286):**
```python
standard_cost = models.DecimalField(...)      # Planned/standard cost
last_purchase_cost = models.DecimalField(...) # Actual last cost
```

**BOMHeader (engineering/models/bom.py:121-148):**
```python
estimated_material_cost = models.DecimalField(...)  # Estimated
total_material_cost = models.DecimalField(...)      # Calculated
```

#### Analysis:
This is **NOT a duplication** - these serve different purposes:
- **BitDesignRevision**: Product cost (what we sell/stock it for)
- **BOMHeader**: Manufacturing cost (what it costs to make)

**VERDICT: ✅ KEEP ALL - Not duplicates, different business concepts**

---

### 3. InventoryStock - Location-Specific Overrides

**Status: ✅ CORRECT DESIGN - Not duplication**

```python
# Item model: Global defaults
reorder_point = models.DecimalField(...)
safety_stock = models.DecimalField(...)

# InventoryStock model: Location-specific overrides
reorder_point = models.DecimalField(..., null=True)  # Override per location
safety_stock = models.DecimalField(..., null=True)   # Override per location
```

This is the **correct pattern**: Global defaults on Item, optional overrides per location on InventoryStock.

**VERDICT: ✅ KEEP - Intentional override pattern**

---

## 🔍 AREAS REQUIRING INVESTIGATION

### 1. HR - Leave Balance Fields

Need to check if there are overlapping fields like:
- `remaining_days` vs `balance` vs `available_days`

**Action Required**: Audit `floor_app/operations/hr/models/leave.py`

### 2. Maintenance - Asset Status Fields

Check for:
- `status` vs `operational_status` vs `condition`
- `downtime_hours` vs `out_of_service_hours`

**Action Required**: Audit `floor_app/operations/maintenance/models/asset.py`

### 3. Production - Quantity Fields

Check for:
- `quantity_planned` vs `quantity_target` vs `quantity_expected`
- `quantity_actual` vs `quantity_completed` vs `quantity_produced`

**Action Required**: Audit production models

### 4. Quality - Inspection Fields

Check for:
- `inspection_result` vs `quality_status` vs `acceptance_status`

**Action Required**: Audit quality models

---

## 📋 DEDUPLICATION ACTION PLAN

### Phase 1: Immediate - Remove `min_stock_qty` from Item Model

**Priority: HIGH** (clear redundancy, no business logic usage)

**Steps:**
1. ✅ Create data migration to preserve data:
   ```python
   # Migration: Update reorder_point from min_stock_qty where needed
   for item in Item.objects.filter(reorder_point=0, min_stock_qty__gt=0):
       item.reorder_point = item.min_stock_qty
       item.save(update_fields=['reorder_point'])
   ```

2. ✅ Remove field from model:
   ```python
   # In floor_app/operations/inventory/models/item.py
   # DELETE:
   # min_stock_qty = models.DecimalField(...)
   ```

3. ✅ Remove from admin:
   ```python
   # In floor_app/operations/inventory/admin/item.py:35
   # Change:
   'fields': ('min_stock_qty', 'reorder_point', 'reorder_qty', 'safety_stock', 'lead_time_days')
   # To:
   'fields': ('reorder_point', 'reorder_qty', 'safety_stock', 'lead_time_days')
   ```

4. ✅ Remove from forms:
   - Update `floor_app/operations/inventory/forms.py`
   - Remove `min_stock_qty` from any ModelForm Meta fields

5. ✅ Remove from templates:
   - Update `floor_app/operations/inventory/templates/inventory/items/form.html`
   - Update `floor_app/operations/inventory/templates/inventory/items/detail.html`

6. ✅ Create Django migration:
   ```bash
   python manage.py makemigrations inventory --name remove_min_stock_qty
   ```

**Files to Modify:**
- `floor_app/operations/inventory/models/item.py`
- `floor_app/operations/inventory/admin/item.py`
- `floor_app/operations/inventory/forms.py`
- `floor_app/operations/inventory/templates/inventory/items/form.html`
- `floor_app/operations/inventory/templates/inventory/items/detail.html`

### Phase 2: Investigation - Audit Other Models

**Priority: MEDIUM**

For each model category:
1. List all fields
2. Identify semantic duplications
3. Check actual usage in code
4. Document findings
5. Create deduplication plan

**Models to Audit:**
- [ ] HR Leave models
- [ ] Maintenance Asset models
- [ ] Production Job/Work Order models
- [ ] Quality Inspection models
- [ ] Planning KPI models

### Phase 3: Project-Wide Standards

**Priority: MEDIUM**

Create field naming standards to prevent future duplications:

**Standard Field Names:**
- **Quantities**: `quantity` (not `qty`, `amount`, `count`)
- **Status**: `status` (not `state`, `stage`, `phase` - unless different concepts)
- **Dates**: `[action]_date` (e.g., `created_date`, `completed_date`)
- **Times**: `[action]_at` (e.g., `created_at`, `updated_at`)
- **Booleans**: `is_[state]` or `has_[feature]`
- **Costs**: Be specific - `unit_cost`, `total_cost`, `estimated_cost`, `actual_cost`

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Complete When:
- ✅ `min_stock_qty` field removed from Item model
- ✅ Data migrated to `reorder_point` where appropriate
- ✅ Admin interface updated
- ✅ Forms updated
- ✅ Templates updated
- ✅ No references to `min_stock_qty` in codebase
- ✅ Migration runs successfully

### Phase 2 Complete When:
- ✅ All model categories audited
- ✅ Duplications documented
- ✅ Deduplication plans created for each finding

### Phase 3 Complete When:
- ✅ Field naming standards documented
- ✅ Standards applied to new code via code review checklist

---

## 📊 IMPACT ASSESSMENT

### Database Impact:
- **Low**: Removing `min_stock_qty` requires one column drop
- **Data Loss**: None (data migrated to `reorder_point` first)
- **Downtime**: None (migration can run while system is live)

### Code Impact:
- **Low**: Field not used in business logic
- **Admin**: Simple fieldset update
- **Forms**: Remove from field list
- **Templates**: Remove from display

### User Impact:
- **Very Low**: Users currently see both fields
- **Improvement**: Clearer interface with less confusion
- **Training**: None required (just one less field)

---

## 🔧 IMPLEMENTATION CHECKLIST

### Pre-Implementation:
- [ ] Backup database
- [ ] Document current state (screenshots of admin forms)
- [ ] Identify all files referencing `min_stock_qty`
- [ ] Create test cases

### Implementation:
- [ ] Create data migration script
- [ ] Test migration on copy of production data
- [ ] Remove field from model
- [ ] Update admin
- [ ] Update forms
- [ ] Update templates
- [ ] Create Django migration
- [ ] Run tests
- [ ] Code review

### Post-Implementation:
- [ ] Run migration on production
- [ ] Verify data integrity
- [ ] Verify admin interface
- [ ] Verify forms work correctly
- [ ] Update documentation
- [ ] Close task

---

## 📝 NOTES

### Why This Matters:
1. **Data Integrity**: Having two fields for the same concept leads to inconsistency
2. **Maintainability**: Future developers won't know which field to use
3. **Performance**: Fewer fields = smaller table size, faster queries
4. **Clarity**: Clear, unambiguous field names improve code quality

### Best Practices Going Forward:
1. **Before adding a field**: Check if similar field already exists
2. **Field naming**: Use industry-standard terminology (e.g., ROP for Reorder Point)
3. **Documentation**: Clear help_text explaining what field means
4. **Business logic**: Fields should have clear purpose in business processes

---

**Document Created:** 2025-11-20
**Priority:** Phase 1 (min_stock_qty) = HIGH, Phase 2 = MEDIUM
**Owner:** Engineering Team
**Related To:** Model Ownership Refactoring Task

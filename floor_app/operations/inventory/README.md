# PDC Bit Inventory Management System

A comprehensive Django-based inventory management backbone designed specifically for PDC (Polycrystalline Diamond Compact) bit manufacturing and repair operations.

## Overview

This system provides:

- **Design Versioning** - MAT numbers with revision control (L3/L4/L5 design levels)
- **Serialized Asset Tracking** - Individual PDC bits tracked by serial number
- **Non-Serialized Stock** - Cutters, consumables, and tools tracked by quantity
- **Multi-Owner Inventory** - ARDT, ENO, JV partners, customer consignment
- **Condition-Based Tracking** - NEW, RECLAIM_AS_NEW, REGROUND, SCRAP, etc.
- **Bill of Materials** - Production, retrofit, and repair BOMs
- **Full Transaction History** - Complete audit trail for all movements

## Architecture

The inventory system follows **3rd Normal Form (3NF)** with a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                  Layer 6: Transactions                   │
│  (InventoryTransaction - all movements and changes)      │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│                    Layer 5: BOM                          │
│       (BOMHeader, BOMLine - production/repair)           │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│              Layer 4: Flexible Attributes                │
│  (AttributeDefinition, CategoryAttributeMap, Values)     │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│                 Layer 3: Physical Stock                  │
│     (Location, SerialUnit, InventoryStock)               │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│                  Layer 2: Item Master                    │
│          (Item - central product catalog)                │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│                Layer 1: Design Definition                │
│ (BitDesign, BitDesignRevision - MAT/Type/Level)         │
└─────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────┐
│              Layer 0: Reference/Lookup Tables            │
│  (ConditionType, OwnershipType, UoM, ItemCategory)      │
└─────────────────────────────────────────────────────────┘
```

## Key Domain Concepts

### PDC Bit Design Levels

| Level | Name | Description |
|-------|------|-------------|
| **L3** | Bit Head Only | Cutting structure/blade geometry only |
| **L4** | Bit Body (No Cutters) | Body with shank, ready for cutters |
| **L5** | Complete Assembly | Full bit with cutters and all components |

L3/L4 designs can be temporarily promoted to act as L5 for testing or retrofit scenarios.

### MAT Number System

MAT numbers are the **primary design identifiers**:

- Format: `{DesignCode}-{Revision}` (e.g., `HP-X123-M2`)
- Revisions: M0, M1, M2... for sequential changes
- Special: `{MAT}-{SerialNumber}` for serial-specific variants
- Temporary MATs: Used before official L5 assignment
- Supersession: Old MATs can be marked as replaced by new ones

### Ownership & Condition Matrix

**Ownership Types:**
- `ARDT` - Company-owned stock
- `ENO` - Internal reclaimed from obsolete/unused bits
- `LSTK` - Long-term stock keeping partner
- `JV_PARTNER` - Joint venture partner owned
- `CUSTOMER_*` - Customer consignment stock

**Condition Types:**
- `NEW` - Brand new purchased
- `RECLAIM_AS_NEW` - From unused bits, physically new quality
- `USED_REGRINDABLE` - Can be reground
- `REGROUND` - Already reground and qualified
- `UNDER_INSPECTION` - Being evaluated
- `SCRAP` - End of life

**Example Combinations:**
- ENO reclaimed cutters: Condition=`RECLAIM_AS_NEW`, Owner=`ENO`
- New company stock: Condition=`NEW`, Owner=`ARDT`
- Customer consignment: Condition=`NEW`, Owner=`CUSTOMER_ARAMCO`

## Models Reference

### Reference Tables

- **ConditionType** - Physical condition states
- **OwnershipType** - Ownership buckets
- **UnitOfMeasure** - Standard UoMs with conversion support
- **ItemCategory** - Hierarchical categorization with serialization flags

### Bit Design Layer

- **BitDesignLevel** - L3/L4/L5 definitions
- **BitDesignType** - Design families (HDBS, SMI, etc.)
- **BitDesign** - Conceptual design family
- **BitDesignRevision** - Specific MAT number/revision (the key identifier)

### Item Master

- **Item** - Central product catalog linking to design and category

### Physical Stock

- **Location** - Hierarchical storage locations
- **SerialUnit** - Individual serialized items (PDC bits)
- **SerialUnitMATHistory** - MAT change audit trail
- **InventoryStock** - Non-serialized stock by dimension (item + location + condition + ownership)

### Flexible Attributes

- **AttributeDefinition** - Custom attribute definitions
- **CategoryAttributeMap** - Attribute-to-category mapping
- **ItemAttributeValue** - Actual attribute values for items

### Bill of Materials

- **BOMHeader** - BOM definition (production/retrofit/repair)
- **BOMLine** - Component requirements

### Transactions

- **InventoryTransaction** - All movements and changes with audit trail

## Installation & Setup

### 1. Add to INSTALLED_APPS

Already configured in `floor_mgmt/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'floor_app.operations.inventory.apps.InventoryConfig',
    ...
]
```

### 2. Create Migrations

```bash
python manage.py makemigrations inventory
```

### 3. Apply Migrations

```bash
python manage.py migrate inventory
```

### 4. Load Initial Data

```bash
python manage.py loaddata floor_app/operations/inventory/fixtures/initial_data.json
```

### 5. Access Admin

Visit `/admin/` to manage:
- Reference data (conditions, ownership, categories)
- Bit designs and MAT revisions
- Items and stock
- BOMs and transactions

## Usage Examples

### Create a Bit Design with MAT Revision

```python
from floor_app.operations.inventory.models import (
    BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision
)

# Get lookup values
level_l5 = BitDesignLevel.objects.get(code='L5')
type_hdbs = BitDesignType.objects.get(code='HDBS')

# Create conceptual design
design = BitDesign.objects.create(
    design_code='HP-X123',
    name='8.5" 6-Blade PDC Bit',
    level=level_l5,
    size_inches=8.50,
    connection_type='4-1/2 API REG',
    blade_count=6,
    total_cutter_count=52
)

# Create first revision (M0)
mat_m0 = BitDesignRevision.objects.create(
    mat_number='HP-X123-M0',
    bit_design=design,
    revision_code='M0',
    design_type=type_hdbs,
    is_temporary=False,
    effective_date='2025-01-01'
)

# Create second revision (M1)
mat_m1 = BitDesignRevision.objects.create(
    mat_number='HP-X123-M1',
    bit_design=design,
    revision_code='M1',
    design_type=type_hdbs,
    effective_date='2025-06-01'
)

# Supersede M0 with M1
mat_m0.supersede_with(mat_m1)
```

### Create Item and Track Serialized Bit

```python
from floor_app.operations.inventory.models import (
    Item, ItemCategory, UnitOfMeasure, SerialUnit,
    ConditionType, OwnershipType, Location
)

# Get references
cat_bit = ItemCategory.objects.get(code='BIT_FULL_ASSEMBLY')
uom_pc = UnitOfMeasure.objects.get(code='PC')
cond_new = ConditionType.objects.get(code='NEW')
owner_ardt = OwnershipType.objects.get(code='ARDT')
loc_wh = Location.objects.get(code='WH-MAIN')

# Create item master record
item = Item.objects.create(
    sku='BIT-HP-X123-M1',
    name='8.5" PDC Bit HP-X123-M1',
    short_name='HP-X123-M1',
    category=cat_bit,
    uom=uom_pc,
    bit_design_revision=mat_m1
)

# Create serialized unit
serial_unit = SerialUnit.objects.create(
    item=item,
    serial_number='ABC12345',
    current_mat=mat_m1,
    location=loc_wh,
    condition=cond_new,
    ownership=owner_ardt,
    status='IN_STOCK',
    manufacture_date='2025-01-15'
)
```

### Track Non-Serialized Stock (Cutters)

```python
# Create cutter item
cat_cutter = ItemCategory.objects.get(code='CUTTER')
cutter_item = Item.objects.create(
    sku='CUT-13MM-STD',
    name='13mm Standard PDC Cutter',
    short_name='13mm Cutter',
    category=cat_cutter,
    uom=uom_pc
)

# Track stock with condition and ownership
cond_reclaim = ConditionType.objects.get(code='RECLAIM_AS_NEW')
owner_eno = OwnershipType.objects.get(code='ENO')

# ENO reclaimed cutters
InventoryStock.objects.create(
    item=cutter_item,
    location=loc_wh,
    condition=cond_reclaim,
    ownership=owner_eno,
    quantity_on_hand=50,
    quantity_reserved=10
)

# Check available
stock = InventoryStock.objects.get(
    item=cutter_item, condition=cond_reclaim, ownership=owner_eno
)
print(f"Available: {stock.quantity_available}")  # 40
```

### Create Production BOM

```python
from floor_app.operations.inventory.models import BOMHeader, BOMLine

bom = BOMHeader.objects.create(
    bom_number='BOM-HP-X123-M1-PROD',
    name='Production BOM for HP-X123-M1',
    bom_type='PRODUCTION',
    target_mat=mat_m1,
    status='ACTIVE',
    effective_date='2025-01-01'
)

# Add cutter component
BOMLine.objects.create(
    bom_header=bom,
    line_number=10,
    component_item=cutter_item,
    quantity_required=52,
    uom=uom_pc,
    scrap_factor=5.00,  # 5% extra for waste
    position_reference='All Blades'
)
```

### Record Inventory Transaction

```python
from floor_app.operations.inventory.models import InventoryTransaction

# Issue cutters for production
txn = InventoryTransaction.objects.create(
    transaction_type='ISSUE',
    item=cutter_item,
    quantity=-52,
    uom=uom_pc,
    from_location=loc_wh,
    from_condition=cond_reclaim,
    from_ownership=owner_eno,
    reference_type='JOB_CARD',
    reference_id='JC-2025-001',
    unit_cost=150.00,
    reason_code='PRODUCTION',
    notes='Issued for HP-X123-M1 production'
)

print(f"Transaction: {txn.transaction_number}")
```

### Retrofit a Bit (MAT Change)

```python
# Change serial unit's MAT from M1 to M2
mat_m2 = BitDesignRevision.objects.get(mat_number='HP-X123-M2')

serial_unit.change_mat(
    new_mat=mat_m2,
    reason='RETROFIT',
    user=request.user,
    notes='Upgraded cutter configuration'
)

# MAT history is automatically recorded
for history in serial_unit.mat_history.all():
    print(f"{history.changed_at}: {history.old_mat} -> {history.new_mat}")
```

## Future Integration Points

The schema is designed to integrate with:

### Batch & Job Card System

Transaction model has placeholder fields:
- `batch_id` - For batch/order grouping
- `job_card_id` - For per-bit job tracking
- `work_order_id` - For work orders

These will be replaced with proper FKs when those models are implemented.

### QR Code Service

The system is designed to NOT include QR logic - that will be handled by a separate central QR service. Models are linkable via:
- `SerialUnit.serial_number`
- `Item.sku`
- `BitDesignRevision.mat_number`

### Cost Accounting

Transaction model includes:
- `unit_cost`, `total_cost`, `currency`
- Links to reference documents (PO, WO, invoice)

## Best Practices

1. **Always use lookup tables** - Don't hardcode condition/ownership values
2. **Link to MAT revisions** - Use `BitDesignRevision` (not just text) for design references
3. **Record transactions** - Log all stock movements for audit trail
4. **Validate at model level** - Use `clean()` methods for business rules
5. **Use soft delete** - Models inherit `SoftDeleteMixin` for recoverability

## File Structure

```
floor_app/operations/inventory/
├── __init__.py
├── apps.py                      # Django app config
├── models/
│   ├── __init__.py             # Model exports
│   ├── reference.py            # Lookup tables
│   ├── bit_design.py           # Design layer
│   ├── item.py                 # Item master
│   ├── stock.py                # Physical stock
│   ├── attributes.py           # EAV system
│   ├── bom.py                  # Bill of materials
│   └── transactions.py         # Transaction log
├── admin/
│   ├── __init__.py
│   ├── reference.py
│   ├── bit_design.py
│   ├── item.py
│   ├── stock.py
│   ├── bom.py
│   └── transactions.py
├── migrations/
│   └── __init__.py
├── fixtures/
│   └── initial_data.json       # Seed data
└── README.md                   # This file
```

## Database Tables

All tables use the prefix `inventory_`:

- `inventory_condition_type`
- `inventory_ownership_type`
- `inventory_unit_of_measure`
- `inventory_item_category`
- `inventory_bit_design_level`
- `inventory_bit_design_type`
- `inventory_bit_design`
- `inventory_bit_design_revision`
- `inventory_item`
- `inventory_location`
- `inventory_serial_unit`
- `inventory_serial_unit_mat_history`
- `inventory_stock`
- `inventory_attribute_definition`
- `inventory_category_attribute_map`
- `inventory_item_attribute_value`
- `inventory_bom_header`
- `inventory_bom_line`
- `inventory_transaction`

## Support

For questions or issues, contact the development team or refer to Django documentation for model management.

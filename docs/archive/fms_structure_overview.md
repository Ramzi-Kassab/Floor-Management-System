# Floor Management System - Technical Structure Overview

**Generated:** 2025-11-20
**Purpose:** Comprehensive analysis for domain redesign and refactoring
**Analyst:** Claude Code (AI Assistant)

---

## Table of Contents

1. [Apps and Modules](#1-apps-and-modules)
2. [Models by App](#2-models-by-app)
3. [Misplaced Responsibilities](#3-misplaced-responsibilities)
4. [Critical Views and Forms](#4-critical-views-and-forms)
5. [Department Ownership Mapping](#5-department-ownership-mapping)
6. [Recommendations](#6-recommendations)

---

## 1. Apps and Modules

### Top-Level Apps

| App | Path | Description |
|-----|------|-------------|
| **floor_app** | `floor_app/` | Main application container |
| **core** | `core/` | Core models (UserPreference, CostCenter, ERP integration, approvals) |

### Nested Apps (under `floor_app/operations/`)

| App | Description | Primary Domain |
|-----|-------------|----------------|
| **analytics** | Analytics, event tracking, automation rules | Business Intelligence |
| **approvals** | Approval workflows | Cross-functional |
| **chat** | Internal messaging | Communication |
| **data_extraction** | Data import/export utilities | IT/Integration |
| **device_tracking** | Device/equipment tracking | IT/Operations |
| **evaluation** | Bit evaluation and inspection | Technical/QA |
| **fives** | 5S workplace organization | Operations |
| **gps_system** | GPS tracking | Logistics |
| **hiring** | Recruitment management | HR |
| **hoc** | HOC (unclear - possibly Hall of Champions?) | HR/Operations |
| **hr** | Human Resources - employees, training, attendance | HR |
| **hr_assets** | HR-related asset tracking | HR |
| **inventory** | ⚠️ **CONTAINS MISPLACED MODELS** - Items, stock, BOM, BitDesign | Inventory + Engineering (mixed) |
| **journey_management** | Travel/journey tracking | HSE/Logistics |
| **knowledge** | Knowledge base, documents, FAQs | Knowledge Management |
| **maintenance** | Equipment maintenance, work orders, downtime | Maintenance |
| **meetings** | Meeting management | Communication |
| **notifications** | User notifications | Cross-functional |
| **planning** | Production planning, scheduling | Production Planning |
| **production** | Job cards, batch orders, routing, quotations | Production |
| **purchasing** | Purchase orders, suppliers, receipts | Procurement |
| **qrcodes** | QR code generation and scanning | Operations |
| **qr_system** | QR system (duplicate?) | Operations |
| **quality** | ⚠️ **CONTAINS FINANCIAL FIELDS** - NCR, CAPA, calibration | Quality Assurance |
| **retrieval** | (No models - placeholder?) | Unknown |
| **sales** | Customers, orders, drilling data, bit lifecycle | Sales/Field Service |
| **user_preferences** | User UI preferences | IT/UX |
| **utility_tools** | Utility functions | IT |
| **vendor_portal** | Vendor self-service portal | Procurement |

**Total Apps:** 32 (2 top-level + 30 nested)

---

## 2. Models by App

### 2.1 Core App

**Location:** `core/models.py`

#### UserPreference
**Purpose:** User interface settings and preferences

| Field | Type | Description |
|-------|------|-------------|
| user | OneToOneField(User) | PK - User account |
| theme | CharField | light/dark/high_contrast |
| font_size | CharField | UI font size |
| table_density | CharField | Table row spacing |
| table_columns_config | JSONField | Saved column configurations |
| sidebar_collapsed | BooleanField | Sidebar state |
| email_notifications | BooleanField | Email notification preference |

#### CostCenter
**Purpose:** Financial tracking and budgeting hierarchy

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Cost center code |
| name | CharField(200) | Cost center name |
| erp_cost_center_code | CharField(50) | ERP system code |
| parent | ForeignKey(self) | Hierarchical parent |
| manager | ForeignKey(User) | Responsible manager |
| annual_budget | DecimalField(15,2) | Annual budget amount |
| currency | CharField(3) | ISO 4217 currency code |
| is_active | BooleanField | Active status |

**Relationships:** Self-referential hierarchy

#### ERPDocumentType
**Purpose:** ERP document type definitions

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | Document type code |
| name | CharField(100) | Document type name |
| erp_system | CharField(50) | ERP system identifier |
| description | TextField | Detailed description |

#### ERPReference
**Purpose:** Generic foreign key to link any model to ERP documents

| Field | Type | Description |
|-------|------|-------------|
| content_type | ForeignKey(ContentType) | GenericFK content type |
| object_id | BigIntegerField | GenericFK object ID |
| document_type | ForeignKey(ERPDocumentType) | ERP document type |
| erp_number | CharField(100) | ERP document number |
| erp_line_number | IntegerField | Line number within document |
| sync_status | CharField(20) | PENDING/SYNCED/FAILED/MANUAL |
| last_sync_at | DateTimeField | Last sync timestamp |

**Relationships:** Generic FK to any model, FK to ERPDocumentType

#### LossOfSaleCause
**Purpose:** Categorization of sales loss reasons

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Cause code |
| category | CharField(50) | stockout/breakdown/delay/quality/other |
| name | CharField(200) | Cause name |
| description | TextField | Detailed description |

#### LossOfSaleEvent
**Purpose:** Track lost sales opportunities with financial impact

| Field | Type | Description |
|-------|------|-------------|
| reference_number | CharField(100, unique) | Event reference |
| cause | ForeignKey(LossOfSaleCause) | Loss cause |
| event_date | DateField | When loss occurred |
| estimated_loss_amount | DecimalField(15,2) | Financial impact |
| cost_center | ForeignKey(CostCenter) | Responsible cost center |
| customer_name | CharField(200) | Affected customer |
| notes | TextField | Additional details |

**Relationships:** FK to LossOfSaleCause, FK to CostCenter

#### ApprovalType
**Purpose:** Define approval workflow types

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Approval type code |
| name | CharField(200) | Approval type name |
| description | TextField | Workflow description |

#### ApprovalAuthority
**Purpose:** Define approval limits by user and type

| Field | Type | Description |
|-------|------|-------------|
| approval_type | ForeignKey(ApprovalType) | Type of approval |
| user | ForeignKey(User) | Authorized user |
| min_amount | DecimalField(15,2) | Minimum approval amount |
| max_amount | DecimalField(15,2) | Maximum approval amount |
| is_active | BooleanField | Active status |

**Relationships:** FK to ApprovalType, FK to User

#### Currency
**Purpose:** Currency master data

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(3, PK) | ISO 4217 code (USD, SAR, EUR) |
| name | CharField(100) | Currency name |
| symbol | CharField(10) | Currency symbol ($, ر.س, €) |
| is_base_currency | BooleanField | System base currency flag |

#### ExchangeRate
**Purpose:** Currency conversion rates

| Field | Type | Description |
|-------|------|-------------|
| from_currency | ForeignKey(Currency) | Source currency |
| to_currency | ForeignKey(Currency) | Target currency |
| rate | DecimalField(15,6) | Exchange rate |
| effective_date | DateField | Rate effective date |

**Relationships:** FK to Currency (2x)

#### Notification
**Purpose:** User notification system

| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | Recipient user |
| notification_type | CharField(20) | INFO/SUCCESS/WARNING/ERROR/TASK/APPROVAL |
| priority | CharField(10) | LOW/NORMAL/HIGH/URGENT |
| title | CharField(200) | Notification title |
| message | TextField | Notification content |
| is_read | BooleanField | Read status |
| action_url | CharField(500) | Link to related item |
| created_at | DateTimeField | Created timestamp |

**Relationships:** FK to User

#### ActivityLog
**Purpose:** System-wide audit trail

| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey(User) | User who performed action |
| action | CharField(50) | CREATE/UPDATE/DELETE/APPROVE/REJECT/etc. |
| description | TextField | Action description |
| content_type | ForeignKey(ContentType) | GenericFK to affected model |
| object_id | BigIntegerField | GenericFK to affected record |
| ip_address | GenericIPAddressField | User IP address |
| timestamp | DateTimeField | Action timestamp |
| changes_json | JSONField | Before/after data |

**Relationships:** FK to User, GenericFK to any model

---

### 2.2 Operations Shared Models

**Location:** `floor_app/operations/models.py`

#### Address
**Purpose:** Generic address model for multiple entities (supports KSA National Address)

| Field | Type | Description |
|-------|------|-------------|
| address_line1 | CharField(200) | Primary address line |
| address_line2 | CharField(200) | Secondary address line |
| city | CharField(100) | City name |
| state_region | CharField(100) | State/province/region |
| postal_code | CharField(20) | Postal/ZIP code |
| country_iso2 | CharField(2) | ISO 3166-1 alpha-2 country code |
| latitude | DecimalField(9,6) | GPS latitude |
| longitude | DecimalField(9,6) | GPS longitude |
| address_kind | CharField(20) | STREET/PO_BOX |
| street_name | CharField(200) | KSA: Street name |
| building_number | CharField(10) | KSA: Building number (4 digits) |
| unit_number | CharField(10) | KSA: Unit number |
| neighborhood | CharField(100) | KSA: Neighborhood |
| additional_number | CharField(4) | KSA: Additional number |
| hr_person | ForeignKey(HRPeople) | For HR address usage |
| hr_kind | CharField(20) | HOME/OFFICE/BILLING/SHIPPING |

**Relationships:** FK to hr.HRPeople (nullable)

---

### 2.3 Inventory App ⚠️ CONTAINS MISPLACED MODELS

**Location:** `floor_app/operations/inventory/models/`

#### Reference/Master Data Models

##### ConditionType
**Purpose:** Define item condition states

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | NEW/RECLAIM_AS_NEW/USED_REGRINDABLE/REGROUND/SCRAP |
| name | CharField(100) | Condition name |
| description | TextField | Condition description |
| is_usable | BooleanField | Can be used in production |
| is_regrindable | BooleanField | Can be reground |
| sort_order | IntegerField | Display order |

##### OwnershipType
**Purpose:** Define item ownership categories

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | ARDT/ENO/LSTK/JV_PARTNER/CUSTOMER_ARAMCO |
| name | CharField(100) | Ownership type name |
| is_internal | BooleanField | Owned by company |
| is_consignment | BooleanField | Consignment stock |
| description | TextField | Detailed description |

##### UnitOfMeasure
**Purpose:** Unit of measure definitions with conversion

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | PC/KG/L/M/SET/BOX |
| name | CharField(100) | UOM full name |
| uom_type | CharField(20) | COUNT/WEIGHT/VOLUME/LENGTH |
| base_uom | ForeignKey(self) | Base UOM for conversion |
| conversion_factor | DecimalField(15,6) | Conversion to base UOM |
| symbol | CharField(10) | Display symbol |

**Relationships:** Self-referential for UOM conversion

##### ItemCategory
**Purpose:** Hierarchical item categorization

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | BIT_FULL_ASSEMBLY/CUTTER/CONSUMABLE/TOOL/PPE |
| name | CharField(200) | Category name |
| parent_category | ForeignKey(self) | Hierarchical parent |
| description | TextField | Category description |
| is_serialized | BooleanField | Requires serial number tracking |
| is_bit_related | BooleanField | PDC bit related category |
| erp_category_code | CharField(50) | ERP mapping |

**Relationships:** Self-referential hierarchy

---

#### ⚠️ BIT DESIGN MODELS - SHOULD BE IN ENGINEERING APP

##### BitDesignLevel
**Purpose:** Design sophistication levels

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(10, unique) | L3/L4/L5 |
| name | CharField(100) | Level name |
| description | TextField | Level description |

**⚠️ ISSUE:** This is engineering/technical data, not inventory

##### BitDesignType
**Purpose:** Design family types

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | HDBS/SMI |
| name | CharField(100) | Type name |
| description | TextField | Type description |

**⚠️ ISSUE:** This is engineering/technical data, not inventory

##### BitDesign
**Purpose:** Conceptual bit design (family)

| Field | Type | Description |
|-------|------|-------------|
| bit_category | CharField(20) | PDC/ROLLER_CONE |
| design_code | CharField(50, unique) | Design family code |
| level | ForeignKey(BitDesignLevel) | Design sophistication |
| size_inches | DecimalField(5,3) | Bit size |
| connection_type | CharField(50) | Thread connection |
| blade_count | IntegerField | Number of blades |
| total_cutter_count | IntegerField | Total cutters |
| nozzle_count | IntegerField | Number of nozzles |
| description | TextField | Design description |
| is_active | BooleanField | Active design |

**Relationships:** FK to BitDesignLevel

**⚠️ ISSUE:** This is engineering/technical data, not inventory

##### BitDesignRevision (MAT Number)
**Purpose:** Specific bit design revision - THE KEY IDENTIFIER for PDC bits

| Field | Type | Description |
|-------|------|-------------|
| mat_number | CharField(50, unique) | **CRITICAL: HP-X123-M2** |
| bit_design | ForeignKey(BitDesign) | Parent design family |
| revision_code | CharField(10) | M0/M1/M2/M3... |
| design_type | ForeignKey(BitDesignType) | HDBS/SMI |
| is_temporary | BooleanField | Temporary MAT flag |
| is_active | BooleanField | Active revision |
| superseded_by | ForeignKey(self) | Replacement MAT |
| effective_date | DateField | When MAT became active |
| erp_item_number | CharField(50) | ERP item master link |
| erp_bom_number | CharField(50) | ERP BOM link |
| **standard_cost** | **DecimalField(12,2)** | **⚠️ Cost data in design model** |
| **last_purchase_cost** | **DecimalField(12,2)** | **⚠️ Cost data in design model** |
| currency | CharField(3) | Currency for costs |
| notes | TextField | Revision notes |

**Relationships:** FK to BitDesign, FK to BitDesignType, Self-FK for superseded_by

**⚠️ CRITICAL ISSUES:**
1. This is engineering/technical data, not inventory
2. Contains cost/pricing fields that should be in finance/costing module
3. This model is referenced everywhere (Item, SerialUnit, JobCard, BOM)

---

#### Item Master

##### Item
**Purpose:** Universal product catalog (items, parts, assemblies, bits)

| Field | Type | Description |
|-------|------|-------------|
| sku | CharField(100, unique) | Stock keeping unit |
| name | CharField(200) | Item name |
| description | TextField | Detailed description |
| category | ForeignKey(ItemCategory) | Item classification |
| uom | ForeignKey(UnitOfMeasure) | Base unit of measure |
| bit_design_revision | ForeignKey(BitDesignRevision) | For PDC bit items (nullable) |
| min_stock_qty | DecimalField(12,4) | Minimum stock level |
| reorder_point | DecimalField(12,4) | Reorder trigger level |
| reorder_qty | DecimalField(12,4) | Standard order quantity |
| safety_stock | DecimalField(12,4) | Safety stock level |
| lead_time_days | IntegerField | Procurement lead time |
| **standard_cost** | **DecimalField(12,2)** | **Standard unit cost** |
| **last_purchase_cost** | **DecimalField(12,2)** | **Most recent purchase cost** |
| currency | CharField(3) | Currency for costs |
| is_active | BooleanField | Active item |
| is_purchasable | BooleanField | Can be purchased |
| is_producible | BooleanField | Can be manufactured |
| is_sellable | BooleanField | Can be sold |
| is_stockable | BooleanField | Inventory tracked |
| primary_supplier | CharField(200) | Default supplier |
| manufacturer_part_number | CharField(100) | MFG part number |
| manufacturer_name | CharField(200) | Manufacturer name |
| weight_kg | DecimalField(10,4) | Item weight |
| volume_cbm | DecimalField(10,6) | Item volume |
| barcode | CharField(100) | Barcode/GTIN |
| erp_item_number | CharField(50) | ERP item code |

**Relationships:** FK to ItemCategory, FK to UnitOfMeasure, FK to BitDesignRevision

**Note:** Standard cost here is acceptable for inventory valuation

---

#### Stock/Inventory Models

##### Location
**Purpose:** Warehouse/bin hierarchy and external locations

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Location code |
| name | CharField(200) | Location name |
| location_type | CharField(30) | WAREHOUSE/ZONE/BIN/RIG/CUSTOMER_SITE/REPAIR_SHOP |
| parent_location | ForeignKey(self) | Hierarchical parent |
| description | TextField | Location description |
| is_active | BooleanField | Active location |
| max_capacity | DecimalField(12,4) | Maximum capacity |
| capacity_uom | ForeignKey(UnitOfMeasure) | Capacity unit |
| address | CharField(500) | Physical address |

**Relationships:** Self-referential hierarchy, FK to UnitOfMeasure

##### SerialUnit
**Purpose:** Individual serialized items (primarily PDC bits)

| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey(Item) | Item master record |
| serial_number | CharField(100, unique) | **Unique serial number** |
| current_mat | ForeignKey(BitDesignRevision) | **Current MAT (can change via retrofit)** |
| location | ForeignKey(Location) | Current location |
| condition | ForeignKey(ConditionType) | Current condition |
| ownership | ForeignKey(OwnershipType) | Ownership type |
| status | CharField(30) | IN_STOCK/RESERVED/AT_RIG/UNDER_REPAIR/SCRAPPED/SOLD |
| manufacture_date | DateField | Manufacturing date |
| received_date | DateField | Received into inventory |
| last_run_date | DateField | Last usage date |
| warranty_expiry | DateField | Warranty expiration |
| total_run_hours | DecimalField(10,2) | Cumulative runtime |
| total_footage_drilled | DecimalField(12,2) | Total footage |
| run_count | IntegerField | Number of runs |
| **acquisition_cost** | **DecimalField(12,2)** | **Original cost** |
| **current_book_value** | **DecimalField(12,2)** | **Depreciated value** |
| current_customer | CharField(200) | If at customer site |
| current_job_reference | CharField(100) | Current job |
| notes | TextField | Additional notes |

**Relationships:** FK to Item, FK to BitDesignRevision, FK to Location, FK to ConditionType, FK to OwnershipType

**Key Feature:** `current_mat` can differ from `item.bit_design_revision` due to retrofits

##### SerialUnitMATHistory
**Purpose:** Audit trail for MAT changes (retrofits, corrections)

| Field | Type | Description |
|-------|------|-------------|
| serial_unit | ForeignKey(SerialUnit) | Serial unit affected |
| old_mat | ForeignKey(BitDesignRevision) | Previous MAT |
| new_mat | ForeignKey(BitDesignRevision) | New MAT |
| reason | CharField(50) | RETROFIT/CORRECTION/UPGRADE/DOWNGRADE/TESTING |
| change_date | DateTimeField | When changed |
| changed_by | ForeignKey(User) | Who changed it |
| notes | TextField | Change notes |

**Relationships:** FK to SerialUnit, FK to BitDesignRevision (2x), FK to User

##### InventoryStock
**Purpose:** Non-serialized item quantity tracking

| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey(Item) | Item tracked |
| location | ForeignKey(Location) | Storage location |
| condition | ForeignKey(ConditionType) | Item condition |
| ownership | ForeignKey(OwnershipType) | Ownership type |
| quantity_on_hand | DecimalField(15,4) | Available qty |
| quantity_reserved | DecimalField(15,4) | Reserved for orders |
| quantity_on_order | DecimalField(15,4) | Incoming qty |
| reorder_point | DecimalField(15,4) | Reorder trigger |
| safety_stock | DecimalField(15,4) | Safety stock |
| **unit_cost** | **DecimalField(12,2)** | **Average unit cost** |
| last_counted_at | DateTimeField | Last physical count |
| last_movement_at | DateTimeField | Last transaction |

**Relationships:** FK to Item, FK to Location, FK to ConditionType, FK to OwnershipType

---

#### Attribute Models (EAV Pattern)

##### AttributeDefinition
**Purpose:** Define custom attributes for items

| Field | Type | Description |
|-------|------|-------------|
| attribute_code | CharField(50, unique) | Attribute code |
| attribute_name | CharField(100) | Display name |
| data_type | CharField(20) | TEXT/NUMBER/BOOLEAN/DATE/CHOICE |
| is_required | BooleanField | Required field |
| validation_regex | CharField(200) | Validation pattern |

##### CategoryAttributeMap
**Purpose:** Link attributes to categories

| Field | Type | Description |
|-------|------|-------------|
| category | ForeignKey(ItemCategory) | Item category |
| attribute | ForeignKey(AttributeDefinition) | Attribute |
| is_required | BooleanField | Required for this category |
| display_order | IntegerField | Display order |

**Relationships:** FK to ItemCategory, FK to AttributeDefinition

##### ItemAttributeValue
**Purpose:** Store attribute values for items (EAV)

| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey(Item) | Item |
| attribute | ForeignKey(AttributeDefinition) | Attribute |
| value | TextField | Attribute value (polymorphic) |

**Relationships:** FK to Item, FK to AttributeDefinition

---

#### ⚠️ BOM MODELS - SHOULD BE IN ENGINEERING APP

##### BOMHeader
**Purpose:** Bill of Materials header

| Field | Type | Description |
|-------|------|-------------|
| bom_number | CharField(50, unique) | BOM identifier |
| name | CharField(200) | BOM name |
| bom_type | CharField(30) | PRODUCTION/RETROFIT/REPAIR/TEMPLATE/DISASSEMBLY |
| target_mat | ForeignKey(BitDesignRevision) | MAT being built/repaired |
| revision | CharField(10) | BOM revision (A/B/C) |
| status | CharField(20) | DRAFT/PENDING_APPROVAL/APPROVED/ACTIVE/OBSOLETE |
| effective_date | DateField | When BOM becomes active |
| obsolete_date | DateField | When BOM becomes obsolete |
| is_active | BooleanField | Active BOM |
| superseded_by | ForeignKey(self) | Replacement BOM |
| source_mat | ForeignKey(BitDesignRevision) | For RETROFIT BOMs (before MAT) |
| **estimated_labor_hours** | **DecimalField(10,2)** | **⚠️ Costing data** |
| **estimated_material_cost** | **DecimalField(12,2)** | **⚠️ Costing data** |
| **total_material_cost** | **DecimalField(12,2)** | **⚠️ Costing data** |
| erp_bom_number | CharField(50) | ERP BOM reference |
| created_by | ForeignKey(User) | BOM creator |
| approved_by | ForeignKey(User) | BOM approver |
| notes | TextField | BOM notes |

**Relationships:** FK to BitDesignRevision (2x: target_mat, source_mat), Self-FK for superseded_by, FK to User (2x)

**⚠️ CRITICAL ISSUES:**
1. BOM is engineering/technical data, not inventory
2. Contains cost/labor estimation fields that should be in separate costing module
3. BOM should be owned by Engineering, not Inventory

##### BOMLine
**Purpose:** BOM component lines

| Field | Type | Description |
|-------|------|-------------|
| bom_header | ForeignKey(BOMHeader) | Parent BOM |
| line_number | IntegerField | Line sequence |
| component_item | ForeignKey(Item) | Component part |
| quantity_required | DecimalField(12,4) | Quantity per assembly |
| uom | ForeignKey(UnitOfMeasure) | Quantity UOM |
| required_condition | ForeignKey(ConditionType) | Required condition |
| required_ownership | ForeignKey(OwnershipType) | Required ownership |
| is_optional | BooleanField | Optional component |
| is_alternative | BooleanField | Alternative component |
| alternative_group | CharField(20) | Alternative group ID |
| scrap_factor | DecimalField(5,2) | Expected scrap % |
| position_reference | CharField(100) | Position (e.g., "Blade 1 Pos 3") |
| **unit_cost** | **DecimalField(12,2)** | **⚠️ Cost per unit** |
| notes | TextField | Line notes |

**Relationships:** FK to BOMHeader, FK to Item, FK to UnitOfMeasure, FK to ConditionType, FK to OwnershipType

**⚠️ ISSUE:** Cost field should not be stored in BOM - should be calculated from Item.standard_cost

---

#### Cutter-Specific Models

##### CutterOwnershipCategory
**Purpose:** Cutter-specific ownership tracking for consumption

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | ENO_AS_NEW/ENO_GROUND/ARDT_RECLAIM/LSTK_RECLAIM/NEW_STOCK/RETROFIT |
| name | CharField(100) | Category name |
| consumption_priority | IntegerField | Consumption order |
| is_new_stock | BooleanField | New cutter stock |
| is_reclaimed | BooleanField | Reclaimed cutter |
| is_ground | BooleanField | Ground cutter |
| excel_column_label | CharField(10) | Excel export column |

##### CutterDetail
**Purpose:** OneToOne extension of Item for cutters

| Field | Type | Description |
|-------|------|-------------|
| item | OneToOneField(Item, PK) | Base item record |
| sap_number | CharField(50, unique) | SAP cutter number |
| cutter_type | CharField(50) | Round/IA-STL/Shyfter/Short Bullet |
| cutter_size | CharField(50) | 1313/1308/13MM Long/1613/19MM |
| grade | CharField(50) | CT97/ELITE RC/M1/CT62/CT36 |
| chamfer | CharField(50) | 0.010"/0.018"/0.012R |
| category | CharField(50) | P-Premium/S-Super Premium/B-Standard/O-Other/D-Depth of Cut |
| replacement_cutter | ForeignKey(Item) | Replacement part |
| is_obsolete | BooleanField | Obsolete cutter |

**Relationships:** OneToOne to Item, FK to Item (replacement)

##### CutterPriceHistory
**Purpose:** Time-based cutter pricing

| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey(Item) | Cutter item |
| effective_date | DateField | Price effective date |
| **unit_price** | **DecimalField(12,2)** | **Unit price** |
| currency | CharField(3) | Price currency |
| source | CharField(20) | PO/MANUAL/IMPORT/CONTRACT |
| notes | TextField | Price notes |

**Relationships:** FK to Item

##### CutterInventorySummary
**Purpose:** Computed cutter inventory levels by ownership

| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey(Item) | Cutter item |
| ownership_category | ForeignKey(CutterOwnershipCategory) | Ownership type |
| current_balance | DecimalField(15,4) | Current quantity |
| consumption_6month | DecimalField(15,4) | 6-month usage |
| consumption_3month | DecimalField(15,4) | 3-month usage |
| consumption_2month | DecimalField(15,4) | 2-month usage |
| safety_stock | DecimalField(15,4) | Safety stock level |
| bom_requirement | DecimalField(15,4) | BOM demand |
| on_order | DecimalField(15,4) | Incoming quantity |
| forecast | DecimalField(15,4) | Forecasted demand |
| status | CharField(20) | OK/LOW/SHORTAGE/EXCESS |
| last_updated | DateTimeField | Last calculation |

**Relationships:** FK to Item, FK to CutterOwnershipCategory

##### CutterBOMGridHeader
**Purpose:** Cutter BOM grid template header

##### CutterBOMGridCell
**Purpose:** Cutter BOM grid cell data

##### CutterBOMSummary
**Purpose:** Aggregated cutter BOM data

##### CutterMapHeader
**Purpose:** Cutter layout map header

##### CutterMapCell
**Purpose:** Cutter position mapping

##### BOMUsageTracking
**Purpose:** Track BOM usage history

---

#### Roller Cone Models

##### RollerConeBitType
**Purpose:** IADC roller cone classification

| Field | Type | Description |
|-------|------|-------------|
| iadc_code | CharField(10, unique) | 111/437/537/617 |
| formation_type | CharField(50) | Soft/Medium/Hard |
| tooth_type | CharField(20) | MILLED/INSERT |
| description | TextField | Type description |

##### RollerConeBearing
**Purpose:** Bearing type definitions

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | Bearing code |
| bearing_type | CharField(50) | OPEN_ROLLER/SEALED_ROLLER/JOURNAL |
| is_sealed | BooleanField | Sealed bearing |
| description | TextField | Bearing description |

##### RollerConeSeal
**Purpose:** Seal type definitions

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | Seal code |
| seal_type | CharField(50) | METAL_FACE/O_RING/HYBRID/NONE |
| description | TextField | Seal description |

##### RollerConeDesign
**Purpose:** Roller cone bit specifications

| Field | Type | Description |
|-------|------|-------------|
| bit_design | OneToOneField(BitDesign) | Parent design |
| number_of_cones | IntegerField | 1-4 cones |
| bit_type | ForeignKey(RollerConeBitType) | IADC classification |
| bearing_type | ForeignKey(RollerConeBearing) | Bearing type |
| seal_type | ForeignKey(RollerConeSeal) | Seal type |
| tooth_structure | CharField(20) | MILLED/INSERT/HYBRID |
| total_insert_count | IntegerField | Total inserts |
| journal_angle_1/2/3 | DecimalField(5,2) | Journal angles |
| cone_offset_inches | DecimalField(6,4) | Cone offset |

**Relationships:** OneToOne to BitDesign, FK to RollerConeBitType, FK to RollerConeBearing, FK to RollerConeSeal

**⚠️ ISSUE:** This is engineering/technical data

##### RollerConeComponent
**Purpose:** Roller cone spare parts

| Field | Type | Description |
|-------|------|-------------|
| part_number | CharField(50, unique) | Component part number |
| component_type | CharField(30) | CONE/BEARING_KIT/SEAL_KIT/INSERT/NOZZLE/SHANK |
| description | CharField(200) | Component description |
| **unit_cost** | **DecimalField(12,2)** | **⚠️ Unit cost** |
| inventory_item_id | BigIntegerField | Link to Item (loose coupling) |

**Relationships:** Loose coupling to Item via BigIntegerField

**⚠️ ISSUE:** Cost field here, plus belongs in engineering

##### RollerConeBOM
**Purpose:** Roller cone bill of materials

| Field | Type | Description |
|-------|------|-------------|
| bit_design_revision | ForeignKey(BitDesignRevision) | Target MAT |
| component | ForeignKey(RollerConeComponent) | Component part |
| quantity | DecimalField(10,2) | Quantity required |
| notes | TextField | Usage notes |

**Relationships:** FK to BitDesignRevision, FK to RollerConeComponent

**⚠️ ISSUE:** BOM is engineering data

---

### 2.4 Production App

**Location:** `floor_app/operations/production/models/`

#### Reference Models

##### OperationDefinition
**Purpose:** Define manufacturing operations

| Field | Type | Description |
|-------|------|-------------|
| operation_code | CharField(50, unique) | Operation code |
| operation_name | CharField(200) | Operation name |
| department | CharField(100) | Responsible department |
| standard_time_minutes | DecimalField(10,2) | Standard operation time |
| description | TextField | Operation description |

##### CutterSymbol
**Purpose:** Cutter symbol definitions for layouts

| Field | Type | Description |
|-------|------|-------------|
| symbol_code | CharField(20, unique) | Symbol code |
| symbol_name | CharField(100) | Symbol name |
| description | TextField | Symbol description |

##### ChecklistTemplate
**Purpose:** Quality/process checklist templates

| Field | Type | Description |
|-------|------|-------------|
| template_code | CharField(50, unique) | Template code |
| template_name | CharField(200) | Template name |
| applies_to | CharField(50) | Applicable to which process |

##### ChecklistItemTemplate
**Purpose:** Individual checklist items

| Field | Type | Description |
|-------|------|-------------|
| template | ForeignKey(ChecklistTemplate) | Parent template |
| item_text | CharField(500) | Checklist item text |
| item_order | IntegerField | Display order |

**Relationships:** FK to ChecklistTemplate

---

#### Core Production Models

##### BatchOrder
**Purpose:** Group multiple job cards into batch

| Field | Type | Description |
|-------|------|-------------|
| batch_number | CharField(50, unique) | Batch identifier |
| customer_name | CharField(200) | Customer |
| batch_type | CharField(30) | PRODUCTION/REPAIR/TESTING |
| status | CharField(30) | NEW/IN_PROGRESS/COMPLETED |
| planned_start_date | DateField | Planned start |
| planned_end_date | DateField | Planned end |
| notes | TextField | Batch notes |

##### JobCard (CENTRAL MODEL)
**Purpose:** Per-bit work order tracking - THE HEART OF THE SYSTEM

| Field | Type | Description |
|-------|------|-------------|
| job_card_number | CharField(50, unique) | **Unique job identifier** |
| batch_order | ForeignKey(BatchOrder) | Parent batch |
| serial_unit | ForeignKey(inventory.SerialUnit) | Physical bit being worked on |
| initial_mat | ForeignKey(inventory.BitDesignRevision) | MAT at job start |
| current_mat | ForeignKey(inventory.BitDesignRevision) | MAT at job end (may change) |
| bom_header | ForeignKey(inventory.BOMHeader) | BOM used for this job |
| customer_order_ref | CharField(100) | Customer PO/order reference |
| customer_name | CharField(200) | Customer name |
| bit_size | CharField(20) | Bit size |
| bit_type | CharField(50) | Bit type |
| well_name | CharField(200) | Well name |
| rig_name | CharField(200) | Rig name |
| field_name | CharField(200) | Oil field name |
| job_type | CharField(30) | NEW_PRODUCTION/REPAIR/RETROFIT/TEST_BIT/REWORK |
| rework_of | ForeignKey(self) | If rework, original job |
| status | CharField(50) | NEW/EVALUATION_IN_PROGRESS/AWAITING_MATERIALS/RELEASED_TO_SHOP/IN_PRODUCTION/UNDER_QC/COMPLETE/SCRAPPED |
| priority | CharField(20) | LOW/NORMAL/HIGH/RUSH/CRITICAL |
| created_date | DateTimeField | Job created |
| evaluation_started_at | DateTimeField | Evaluation started |
| evaluation_completed_at | DateTimeField | Evaluation completed |
| released_at | DateTimeField | Released to production |
| production_started_at | DateTimeField | Production started |
| qc_started_at | DateTimeField | QC started |
| completed_at | DateTimeField | Job completed |
| planned_start_date | DateField | Planned start |
| planned_end_date | DateField | Planned end |
| actual_start_date | DateField | Actual start |
| actual_end_date | DateField | Actual end |
| **estimated_cost** | **DecimalField(12,2)** | **Estimated job cost** |
| **actual_cost** | **DecimalField(12,2)** | **Actual job cost** |
| **quoted_price** | **DecimalField(12,2)** | **Price quoted to customer** |
| erp_production_order_number | CharField(50) | ERP production order |
| cost_center | ForeignKey(core.CostCenter) | Cost center |
| notes | TextField | Job notes |

**Relationships:** FK to BatchOrder, FK to SerialUnit, FK to BitDesignRevision (2x), FK to BOMHeader, Self-FK for rework, FK to CostCenter

**⚠️ NOTE:** Cost fields here may be acceptable as production owns job costing

---

#### Routing Models

##### JobRoute
**Purpose:** Routing plan for job

| Field | Type | Description |
|-------|------|-------------|
| job_card | ForeignKey(JobCard) | Parent job |
| route_name | CharField(100) | Route name |
| is_active | BooleanField | Active route |

**Relationships:** FK to JobCard

##### JobRouteStep
**Purpose:** Individual routing steps

| Field | Type | Description |
|-------|------|-------------|
| job_route | ForeignKey(JobRoute) | Parent route |
| step_number | IntegerField | Step sequence |
| operation | ForeignKey(OperationDefinition) | Operation to perform |
| status | CharField(30) | PENDING/IN_PROGRESS/COMPLETED |
| planned_start | DateTimeField | Planned start time |
| actual_start | DateTimeField | Actual start time |
| actual_end | DateTimeField | Actual end time |

**Relationships:** FK to JobRoute, FK to OperationDefinition

---

#### Evaluation Models

##### CutterLayout
**Purpose:** Cutter layout template for bit design

| Field | Type | Description |
|-------|------|-------------|
| bit_design_revision | ForeignKey(inventory.BitDesignRevision) | MAT number |
| layout_name | CharField(100) | Layout name |
| total_positions | IntegerField | Total cutter positions |

**Relationships:** FK to BitDesignRevision

##### CutterLocation
**Purpose:** Individual cutter position in layout

| Field | Type | Description |
|-------|------|-------------|
| layout | ForeignKey(CutterLayout) | Parent layout |
| position_code | CharField(50) | Position identifier |
| blade_number | IntegerField | Blade number |
| row_number | IntegerField | Row number |
| position_number | IntegerField | Position number |
| x_coordinate | DecimalField(10,4) | X position |
| y_coordinate | DecimalField(10,4) | Y position |

**Relationships:** FK to CutterLayout

##### JobCutterEvaluationHeader
**Purpose:** Cutter evaluation session for job

| Field | Type | Description |
|-------|------|-------------|
| job_card | ForeignKey(JobCard) | Job being evaluated |
| evaluation_date | DateField | Evaluation date |
| evaluator | ForeignKey(User) | Who evaluated |
| is_complete | BooleanField | Evaluation complete |

**Relationships:** FK to JobCard, FK to User

##### JobCutterEvaluationDetail
**Purpose:** Per-position cutter evaluation

| Field | Type | Description |
|-------|------|-------------|
| header | ForeignKey(JobCutterEvaluationHeader) | Evaluation session |
| cutter_location | ForeignKey(CutterLocation) | Position evaluated |
| cutter_item | ForeignKey(inventory.Item) | Cutter found |
| condition | ForeignKey(inventory.ConditionType) | Cutter condition |
| ownership | ForeignKey(inventory.OwnershipType) | Cutter ownership |
| action | CharField(30) | REUSE/REGRIND/SCRAP/REPLACE |
| notes | TextField | Evaluation notes |

**Relationships:** FK to JobCutterEvaluationHeader, FK to CutterLocation, FK to Item, FK to ConditionType, FK to OwnershipType

##### JobCutterEvaluationOverride
**Purpose:** Manual overrides to evaluation

| Field | Type | Description |
|-------|------|-------------|
| evaluation_detail | ForeignKey(JobCutterEvaluationDetail) | Detail being overridden |
| original_action | CharField(30) | Original action |
| override_action | CharField(30) | New action |
| override_reason | TextField | Why overridden |
| overridden_by | ForeignKey(User) | Who overrode |
| overridden_at | DateTimeField | When overridden |

**Relationships:** FK to JobCutterEvaluationDetail, FK to User

---

#### Inspection Models

##### ApiThreadInspection
**Purpose:** API thread inspection report

| Field | Type | Description |
|-------|------|-------------|
| job_card | ForeignKey(JobCard) | Job inspected |
| inspector | ForeignKey(User) | Inspector |
| inspection_date | DateField | Inspection date |
| thread_type | CharField(50) | API thread type |
| pass_fail | CharField(10) | PASS/FAIL |
| measurements_json | JSONField | Detailed measurements |
| notes | TextField | Inspection notes |

**Relationships:** FK to JobCard, FK to User

##### NdtReport
**Purpose:** Non-destructive testing report

| Field | Type | Description |
|-------|------|-------------|
| job_card | ForeignKey(JobCard) | Job tested |
| ndt_type | CharField(30) | UT/MT/PT/RT |
| technician | ForeignKey(User) | NDT technician |
| test_date | DateField | Test date |
| pass_fail | CharField(10) | PASS/FAIL |
| defects_found | TextField | Defects description |
| report_file | FileField | Report PDF |

**Relationships:** FK to JobCard, FK to User

---

#### Checklist Models

##### JobChecklistInstance
**Purpose:** Checklist instance for job

| Field | Type | Description |
|-------|------|-------------|
| job_card | ForeignKey(JobCard) | Job |
| template | ForeignKey(ChecklistTemplate) | Template used |
| completed | BooleanField | All items completed |

**Relationships:** FK to JobCard, FK to ChecklistTemplate

##### JobChecklistItem
**Purpose:** Individual checklist item completion

| Field | Type | Description |
|-------|------|-------------|
| instance | ForeignKey(JobChecklistInstance) | Checklist instance |
| template_item | ForeignKey(ChecklistItemTemplate) | Template item |
| is_checked | BooleanField | Item checked |
| checked_by | ForeignKey(User) | Who checked |
| checked_at | DateTimeField | When checked |
| notes | TextField | Notes |

**Relationships:** FK to JobChecklistInstance, FK to ChecklistItemTemplate, FK to User

---

#### Quotation Models

##### Quotation
**Purpose:** Customer quotation/estimate

| Field | Type | Description |
|-------|------|-------------|
| quote_number | CharField(50, unique) | Quote number |
| customer_name | CharField(200) | Customer |
| quote_date | DateField | Quote date |
| valid_until | DateField | Validity date |
| status | CharField(30) | DRAFT/SENT/ACCEPTED/REJECTED |
| **total_amount** | **DecimalField(12,2)** | **Total quote value** |
| notes | TextField | Quote notes |

##### QuotationLine
**Purpose:** Quotation line items

| Field | Type | Description |
|-------|------|-------------|
| quotation | ForeignKey(Quotation) | Parent quote |
| line_number | IntegerField | Line number |
| description | CharField(500) | Item description |
| quantity | DecimalField(10,2) | Quantity |
| **unit_price** | **DecimalField(12,2)** | **Unit price** |
| **line_total** | **DecimalField(12,2)** | **Line total** |

**Relationships:** FK to Quotation

---

### 2.5 Quality App ⚠️ CONTAINS FINANCIAL FIELDS

**Location:** `floor_app/operations/quality/models/`

#### Reference Models

##### DefectCategory
**Purpose:** Categorize defect types

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Defect category code |
| name | CharField(200) | Category name |
| description | TextField | Category description |

##### RootCauseCategory
**Purpose:** Categorize root causes

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Root cause category |
| name | CharField(200) | Category name |
| description | TextField | Category description |

---

#### NCR Models

##### NonconformanceReport ⚠️ FINANCIAL FIELDS ISSUE
**Purpose:** Nonconformance tracking and CAPA

| Field | Type | Description |
|-------|------|-------------|
| ncr_number | CharField(50, unique) | **NCR identifier** |
| ncr_type | CharField(30) | INTERNAL/SUPPLIER/CUSTOMER/PROCESS |
| status | CharField(30) | OPEN/CONTAINED/ROOT_CAUSE/CORRECTIVE/VERIFICATION/CLOSED/CANCELLED |
| job_card_id | BigIntegerField | Loose coupling to JobCard |
| serial_unit_id | BigIntegerField | Loose coupling to SerialUnit |
| batch_order_id | BigIntegerField | Loose coupling to BatchOrder |
| defect_category | ForeignKey(DefectCategory) | Defect type |
| title | CharField(200) | NCR title |
| description | TextField | Detailed description |
| detection_point | CharField(100) | Where detected |
| detection_method | CharField(100) | How detected |
| quantity_affected | PositiveIntegerField | Affected quantity |
| quantity_contained | PositiveIntegerField | Contained quantity |
| severity | CharField(20) | CRITICAL/MAJOR/MINOR |
| customer_impact | BooleanField | Customer affected |
| production_impact | BooleanField | Production affected |
| safety_impact | BooleanField | Safety affected |
| disposition | CharField(30) | PENDING/USE_AS_IS/REWORK/REPAIR/SCRAP/RETURN_SUPPLIER/DOWNGRADE |
| disposition_by | ForeignKey(User) | Who decided disposition |
| disposition_date | DateField | Disposition date |
| **estimated_cost_impact** | **DecimalField(12,2)** | **⚠️ SHOULD NOT BE IN QA** |
| **actual_cost_impact** | **DecimalField(12,2)** | **⚠️ SHOULD NOT BE IN QA** |
| **lost_revenue** | **DecimalField(12,2)** | **⚠️ SHOULD NOT BE IN QA** |
| reported_by | ForeignKey(User) | Reporter |
| reported_date | DateField | Report date |
| assigned_to | ForeignKey(User) | Assigned to |
| target_closure_date | DateField | Target close date |
| actual_closure_date | DateField | Actual close date |
| notes | TextField | Additional notes |

**Relationships:** FK to DefectCategory, FK to User (3x: disposition_by, reported_by, assigned_to)

**⚠️ CRITICAL ISSUE:** NCR model contains financial fields (cost impact, lost revenue) that should NOT be in Quality module. This violates separation of duties and financial controls.

##### NCRRootCauseAnalysis
**Purpose:** 5-Why root cause analysis

| Field | Type | Description |
|-------|------|-------------|
| ncr | ForeignKey(NonconformanceReport) | Parent NCR |
| category | ForeignKey(RootCauseCategory) | Root cause category |
| why_1 | TextField | First why question |
| why_2 | TextField | Second why question |
| why_3 | TextField | Third why question |
| why_4 | TextField | Fourth why question |
| why_5 | TextField | Fifth why question |
| root_cause_statement | TextField | Final root cause |
| is_systemic | BooleanField | Systemic issue |
| analyzed_by | ForeignKey(User) | Analyzer |
| analyzed_date | DateField | Analysis date |

**Relationships:** FK to NonconformanceReport, FK to RootCauseCategory, FK to User

##### NCRCorrectiveAction
**Purpose:** CAPA tracking

| Field | Type | Description |
|-------|------|-------------|
| ncr | ForeignKey(NonconformanceReport) | Parent NCR |
| action_type | CharField(30) | IMMEDIATE/CORRECTIVE/PREVENTIVE |
| description | TextField | Action description |
| assigned_to | ForeignKey(User) | Action owner |
| due_date | DateField | Due date |
| completed_date | DateField | Completion date |
| status | CharField(30) | PENDING/IN_PROGRESS/COMPLETED/VERIFIED/CANCELLED |
| effectiveness_verified | BooleanField | Effectiveness verified |
| verification_date | DateField | Verification date |
| verified_by | ForeignKey(User) | Verifier |
| notes | TextField | Action notes |

**Relationships:** FK to NonconformanceReport, FK to User (2x: assigned_to, verified_by)

---

#### Calibration Models

##### CalibrationSchedule
**Purpose:** Equipment calibration scheduling

| Field | Type | Description |
|-------|------|-------------|
| equipment_id | BigIntegerField | Equipment reference |
| equipment_name | CharField(200) | Equipment name |
| calibration_frequency_days | IntegerField | Calibration interval |
| last_calibration_date | DateField | Last calibration |
| next_calibration_date | DateField | Next due date |
| is_overdue | BooleanField | Overdue flag |

##### CalibrationRecord
**Purpose:** Calibration completion record

| Field | Type | Description |
|-------|------|-------------|
| schedule | ForeignKey(CalibrationSchedule) | Schedule |
| calibration_date | DateField | Calibration date |
| calibrated_by | ForeignKey(User) | Technician |
| certificate_number | CharField(100) | Cal certificate |
| pass_fail | CharField(10) | PASS/FAIL |
| results_json | JSONField | Calibration results |
| certificate_file | FileField | Certificate PDF |

**Relationships:** FK to CalibrationSchedule, FK to User

---

#### Disposition Models

##### DispositionAction
**Purpose:** Track disposition actions from NCRs

| Field | Type | Description |
|-------|------|-------------|
| ncr | ForeignKey(NonconformanceReport) | Parent NCR |
| action_taken | CharField(500) | Disposition action |
| action_date | DateField | Action date |
| performed_by | ForeignKey(User) | Who performed |

**Relationships:** FK to NonconformanceReport, FK to User

---

### 2.6 HR App

**Location:** `floor_app/operations/hr/models/`

**Note:** HR models are in separate files. Full extraction not completed, but key models include:

#### Core HR Models (Partial List)

##### Department
**Purpose:** Organizational departments

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Department code |
| name | CharField(200) | Department name |
| parent | ForeignKey(self) | Parent department |
| manager | ForeignKey(User) | Department manager |

**Relationships:** Self-referential hierarchy, FK to User

##### Position
**Purpose:** Job positions

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(50, unique) | Position code |
| title | CharField(200) | Position title |
| department | ForeignKey(Department) | Department |
| grade_level | CharField(20) | Job grade |

**Relationships:** FK to Department

##### HRPeople
**Purpose:** Person master record (employees, contractors, contacts)

| Field | Type | Description |
|-------|------|-------------|
| person_code | CharField(50, unique) | Person identifier |
| first_name | CharField(100) | First name |
| last_name | CharField(100) | Last name |
| national_id | CharField(50) | National ID |
| date_of_birth | DateField | DOB |
| gender | CharField(10) | M/F/Other |
| nationality | CharField(50) | Nationality |
| person_type | CharField(30) | EMPLOYEE/CONTRACTOR/CONTACT |

##### Employee
**Purpose:** Employee-specific data

| Field | Type | Description |
|-------|------|-------------|
| person | OneToOneField(HRPeople) | Person record |
| employee_number | CharField(50, unique) | Employee number |
| hire_date | DateField | Hire date |
| position | ForeignKey(Position) | Current position |
| employment_status | CharField(30) | ACTIVE/TERMINATED/ON_LEAVE |

**Relationships:** OneToOne to HRPeople, FK to Position

##### Qualification
**Purpose:** Employee qualifications

##### Training
**Purpose:** Training records

##### Leave
**Purpose:** Leave/vacation tracking

##### Attendance
**Purpose:** Daily attendance

##### Document
**Purpose:** Employee documents

##### Email
**Purpose:** Contact emails

##### Phone
**Purpose:** Contact phones

---

### 2.7 Purchasing App

**Location:** `floor_app/operations/purchasing/models/`

#### Supplier Models

##### Supplier
**Purpose:** Supplier/vendor master

| Field | Type | Description |
|-------|------|-------------|
| supplier_code | CharField(50, unique) | Supplier code |
| supplier_name | CharField(200) | Supplier name |
| supplier_type | CharField(30) | MANUFACTURER/DISTRIBUTOR/SERVICE |
| payment_terms | ForeignKey(PaymentTerms) | Default payment terms |
| currency | ForeignKey(Currency) | Default currency |
| is_active | BooleanField | Active supplier |

**Relationships:** FK to PaymentTerms, FK to Currency

##### Currency
**Purpose:** Currency definitions (duplicate of core.Currency?)

##### Incoterms
**Purpose:** International commercial terms

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(10, unique) | Incoterm code (FOB/CIF/EXW) |
| description | CharField(200) | Description |

##### PaymentTerms
**Purpose:** Payment term definitions

| Field | Type | Description |
|-------|------|-------------|
| code | CharField(20, unique) | Terms code (NET30/NET60) |
| description | CharField(200) | Terms description |
| days | IntegerField | Payment days |

---

#### Purchase Order Models

##### PurchaseOrder
**Purpose:** Purchase order header

| Field | Type | Description |
|-------|------|-------------|
| po_number | CharField(50, unique) | **PO number** |
| po_type | CharField(30) | STANDARD/BLANKET/CONTRACT/SCHEDULED |
| status | CharField(30) | DRAFT/PENDING_APPROVAL/APPROVED/SENT/ACKNOWLEDGED/PARTIALLY_RECEIVED/FULLY_RECEIVED/CLOSED/CANCELLED |
| supplier | ForeignKey(Supplier) | Supplier |
| buyer_id | BigIntegerField | Loose coupling to buyer User |
| department_id | BigIntegerField | Loose coupling to Department |
| po_date | DateField | PO date |
| delivery_date | DateField | Required delivery date |
| **total_amount** | **DecimalField(15,2)** | **PO total** |
| currency | ForeignKey(Currency) | PO currency |
| payment_terms | ForeignKey(PaymentTerms) | Payment terms |
| incoterms | ForeignKey(Incoterms) | Shipping terms |
| notes | TextField | PO notes |

**Relationships:** FK to Supplier, FK to Currency, FK to PaymentTerms, FK to Incoterms

##### PurchaseOrderLine
**Purpose:** PO line items

| Field | Type | Description |
|-------|------|-------------|
| po | ForeignKey(PurchaseOrder) | Parent PO |
| line_number | IntegerField | Line number |
| item_id | BigIntegerField | Loose coupling to Item |
| description | CharField(500) | Line description |
| quantity | DecimalField(12,4) | Order quantity |
| uom_code | CharField(20) | Unit of measure |
| **unit_price** | **DecimalField(12,2)** | **Unit price** |
| **line_total** | **DecimalField(15,2)** | **Line total** |
| delivery_date | DateField | Line delivery date |
| quantity_received | DecimalField(12,4) | Received qty |
| quantity_remaining | DecimalField(12,4) | Open qty |

**Relationships:** FK to PurchaseOrder

---

#### Other Purchasing Models

##### Requisition
**Purpose:** Purchase requisition

##### RFQ
**Purpose:** Request for quotation

##### Receipt
**Purpose:** Goods receipt note

##### Returns
**Purpose:** Supplier returns

##### Invoice
**Purpose:** Supplier invoice

##### Shipment
**Purpose:** Shipment tracking

##### Transfer
**Purpose:** Inter-warehouse transfers

---

### 2.8 Planning App

**Location:** `floor_app/operations/planning/models/`

#### Models (High Level)

##### Schedule
**Purpose:** Production schedule

##### Resource
**Purpose:** Resource planning

##### Requirements
**Purpose:** Requirements planning

##### KPI
**Purpose:** KPI definitions

##### Metrics
**Purpose:** Metrics tracking

##### VisualPlanning
**Purpose:** Visual planning tools

---

### 2.9 Sales App

**Location:** `floor_app/operations/sales/models/`

#### Models

##### Customer
**Purpose:** Customer master

| Field | Type | Description |
|-------|------|-------------|
| customer_code | CharField(50, unique) | Customer code |
| customer_name | CharField(200) | Customer name |
| customer_type | CharField(30) | OPERATOR/CONTRACTOR/DISTRIBUTOR |
| payment_terms | ForeignKey(PaymentTerms) | Payment terms |
| currency | ForeignKey(Currency) | Default currency |
| credit_limit | DecimalField(15,2) | Credit limit |

**Relationships:** FK to PaymentTerms, FK to Currency

##### Sales
**Purpose:** Sales orders/quotes

##### Drilling
**Purpose:** Drilling performance data

| Field | Type | Description |
|-------|------|-------------|
| serial_unit_id | BigIntegerField | Bit serial |
| well_name | CharField(200) | Well name |
| rig_name | CharField(200) | Rig name |
| run_date | DateField | Run date |
| footage_drilled | DecimalField(10,2) | Footage |
| hours_drilled | DecimalField(10,2) | Runtime |
| rop_avg | DecimalField(10,2) | Average ROP |

##### DullGrade
**Purpose:** IADC dull grading

| Field | Type | Description |
|-------|------|-------------|
| serial_unit_id | BigIntegerField | Bit serial |
| dull_code | CharField(20) | IADC dull code |
| inner_row | CharField(2) | Inner row grade |
| outer_row | CharField(2) | Outer row grade |
| location | CharField(2) | Dull location |
| bearing_seal | CharField(2) | Bearing/seal grade |
| gauge | CharField(2) | Gauge wear |

##### Lifecycle
**Purpose:** Bit lifecycle tracking

| Field | Type | Description |
|-------|------|-------------|
| serial_unit_id | BigIntegerField | Bit serial |
| lifecycle_stage | CharField(30) | NEW/FIRST_RUN/RERUN/REPAIR/RETIRED |
| stage_date | DateField | Stage date |
| notes | TextField | Stage notes |

---

### 2.10 Maintenance App

**Location:** `floor_app/operations/maintenance/models/`

#### Models (Simplified)

##### Asset
**Purpose:** Physical assets (equipment, tools)

| Field | Type | Description |
|-------|------|-------------|
| asset_code | CharField(50, unique) | Asset code |
| asset_name | CharField(200) | Asset name |
| asset_type | CharField(50) | Asset type |
| location | ForeignKey(Location) | Current location |
| status | CharField(30) | IN_SERVICE/UNDER_MAINTENANCE/OUT_OF_SERVICE |

**Relationships:** FK to inventory.Location

##### MaintenanceRequest
**Purpose:** Maintenance request

##### WorkOrder
**Purpose:** Maintenance work order

| Field | Type | Description |
|-------|------|-------------|
| wo_number | CharField(50, unique) | Work order number |
| asset | ForeignKey(Asset) | Asset |
| wo_type | CharField(30) | CORRECTIVE/PREVENTIVE |
| status | CharField(30) | PLANNED/IN_PROGRESS/COMPLETED |
| **estimated_cost** | **DecimalField(12,2)** | **Estimated cost** |
| **actual_cost** | **DecimalField(12,2)** | **Actual cost** |

**Relationships:** FK to Asset

##### PreventiveMaintenance
**Purpose:** PM schedules

##### DowntimeEvent
**Purpose:** Equipment downtime tracking

| Field | Type | Description |
|-------|------|-------------|
| asset | ForeignKey(Asset) | Asset |
| start_time | DateTimeField | Downtime start |
| end_time | DateTimeField | Downtime end |
| downtime_type | CharField(30) | PLANNED/UNPLANNED |
| reason | TextField | Downtime reason |

**Relationships:** FK to Asset

##### PartsUsage
**Purpose:** Parts consumed in maintenance

---

### 2.11 Evaluation App

**Location:** `floor_app/operations/evaluation/models/`

#### Models

##### Session
**Purpose:** Evaluation session

##### Cell
**Purpose:** Evaluation grid cells

##### Inspection
**Purpose:** Inspection records

##### Instructions
**Purpose:** Technical instructions

##### Reference
**Purpose:** Reference data

##### Audit
**Purpose:** Evaluation audit trail

##### Instances
**Purpose:** Instance tracking

---

### 2.12 Knowledge App

**Location:** `floor_app/operations/knowledge/models/`

#### Models

##### Article
**Purpose:** Knowledge base articles

##### Category
**Purpose:** Article categories

##### Document
**Purpose:** Document repository

##### FAQ
**Purpose:** Frequently asked questions

##### Instruction
**Purpose:** Work instructions

##### Tag
**Purpose:** Tagging system

##### Training
**Purpose:** Training materials

---

### 2.13 QRCodes App

**Location:** `floor_app/operations/qrcodes/models/`

#### Models

##### QCode
**Purpose:** QR code registry

##### ScanLog
**Purpose:** QR scan history

##### Movement
**Purpose:** Movement tracking via QR

##### ProcessExecution
**Purpose:** Process execution via QR

##### Maintenance
**Purpose:** Maintenance via QR

---

### 2.14 Analytics App

**Location:** `floor_app/operations/analytics/models/`

#### Models

##### Event
**Purpose:** Analytics event tracking

##### AutomationRule
**Purpose:** Automation rules

##### InformationRequest
**Purpose:** Information requests

##### Tracking
**Purpose:** Generic tracking

---

## 3. Misplaced Responsibilities

### 🚨 CRITICAL ISSUE #1: BOM/BIT DESIGN MODELS IN INVENTORY APP

**Current Location:** `floor_app/operations/inventory/models/`

**Models That Should Be in Engineering App:**

1. **BitDesignLevel** - Design levels (L3/L4/L5)
2. **BitDesignType** - Design families (HDBS/SMI)
3. **BitDesign** - Conceptual bit design
4. **BitDesignRevision** - **MAT numbers (THE KEY DESIGN IDENTIFIER)**
5. **BOMHeader** - Bill of Materials header
6. **BOMLine** - BOM component lines
7. **RollerConeDesign** - Roller cone specifications
8. **RollerConeBOM** - Roller cone BOM
9. **RollerConeComponent** - Roller cone components

**Why This is Wrong:**

1. **Separation of Concerns**
   - Design/engineering data ≠ Physical inventory
   - BitDesign is "what the design is" (engineering domain)
   - Item/Stock is "what we have physically" (inventory domain)

2. **Organizational Ownership**
   - Engineering department should own design data, BOM data
   - Inventory/warehouse should own stock, locations, movements
   - Mixing responsibilities creates access control issues

3. **Lifecycle Independence**
   - Designs evolve independently from physical stock
   - A design (MAT) can exist before any bits are built
   - A design can become obsolete while bits still exist in stock

4. **Industry Standard Practice**
   - PLM (Product Lifecycle Management) systems are separate from WMS (Warehouse Management)
   - SAP has separate modules: MM (Materials) vs PP-PI (Production Planning)
   - Oracle has PLM Cloud separate from Inventory Management

5. **Maintenance Burden**
   - Inventory team shouldn't need to understand engineering revisions
   - Engineering team shouldn't need inventory module access to create designs

**What Should Happen:**

Create new app: `floor_app/operations/engineering/`

```
engineering/
├── models/
│   ├── __init__.py
│   ├── bit_design.py         ← BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision
│   ├── bom.py                 ← BOMHeader, BOMLine
│   ├── roller_cone.py         ← RollerConeDesign, RollerConeBOM, RollerConeComponent
│   └── specifications.py      ← Future: CAD files, drawings, specs
├── views.py
├── forms.py
├── urls.py
└── admin.py
```

**Dependencies to Fix:**

All these models reference BitDesign/BOM:
- `inventory.Item.bit_design_revision` FK
- `inventory.SerialUnit.current_mat` FK
- `production.JobCard.initial_mat` FK
- `production.JobCard.current_mat` FK
- `production.JobCard.bom_header` FK
- `production.CutterLayout.bit_design_revision` FK

**Migration Path:**

1. Create `engineering` app
2. Copy models to new app with same db_table names
3. Update all imports across codebase
4. Move views, forms, admin, tests
5. Update URL routing
6. Delete models from inventory app

---

### 🚨 CRITICAL ISSUE #2: FINANCIAL FIELDS IN QUALITY NCR MODEL

**Current Location:** `floor_app/operations/quality/models/ncr.py`

**Model:** `NonconformanceReport`

**Problematic Fields (Lines 136-153):**

```python
estimated_cost_impact = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    help_text="Estimated cost of the nonconformance"
)
actual_cost_impact = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    help_text="Actual cost after resolution"
)
lost_revenue = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    help_text="Lost revenue due to this NCR"
)
```

**Why This is Wrong:**

1. **Separation of Duties (SOD)**
   - QA department should NOT calculate or enter financial data
   - Finance/accounting owns all cost and revenue calculations
   - Violates basic financial controls

2. **Audit Requirements**
   - Financial data requires different audit trails
   - QA audit focuses on technical conformance
   - Financial audit focuses on monetary accuracy

3. **SOX Compliance**
   - Mixing quality and financial data violates Sarbanes-Oxley controls
   - Financial data must have segregated access and approval workflows

4. **Domain Logic**
   - Calculating cost impact requires:
     - Access to cost centers and budgets
     - Knowledge of rework labor rates
     - Parts pricing data
     - Overhead allocation rules
   - QA department shouldn't have this data

5. **Approval Authority**
   - Financial impacts require finance manager approval
   - QA disposition requires QA manager approval
   - These are separate approval chains

**What Should Happen:**

**Option A:** Create separate financial impact model in `core` or new `finance` app

```python
# core/models.py or finance/models.py
class NCRFinancialImpact(AuditMixin, models.Model):
    """Financial impact assessment for NCRs - owned by Finance"""

    ncr_id = models.BigIntegerField(
        db_index=True,
        help_text="Loose coupling to quality.NonconformanceReport"
    )

    # Cost fields
    estimated_cost_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lost_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Financial tracking
    cost_center = models.ForeignKey('core.CostCenter', on_delete=models.PROTECT)
    fiscal_period = models.CharField(max_length=20)

    # Approval
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    assessed_at = models.DateTimeField(null=True, blank=True)
    approved_by_finance = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
```

**Option B:** Extend with GenericFK

```python
# core/models.py
class FinancialImpact(AuditMixin, models.Model):
    """Generic financial impact tracking"""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    impact_type = models.CharField(max_length=30)  # NCR/DOWNTIME/REWORK/SCRAP
    estimated_cost = models.DecimalField(max_digits=15, decimal_places=2)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2)
    lost_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    cost_center = models.ForeignKey('CostCenter', on_delete=models.PROTECT)
    # ... approval fields
```

**Migration Steps:**

1. Create new `NCRFinancialImpact` model
2. Write data migration to copy existing cost data
3. Remove cost fields from `NonconformanceReport`
4. Update views/forms to show financial data from new model
5. Implement separate financial approval workflow

---

### ⚠️ ISSUE #3: COST FIELDS IN BIT DESIGN REVISION

**Model:** `inventory.BitDesignRevision`

**Problematic Fields:**

```python
standard_cost = models.DecimalField(max_digits=12, decimal_places=2, ...)
last_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, ...)
```

**Why This is Wrong:**

1. **Design vs Costing**
   - MAT number is a design identifier (engineering domain)
   - Cost is a financial/costing domain
   - Design shouldn't "know" its cost

2. **Multiple Costs**
   - Same MAT can have different costs in different time periods
   - Cost varies by supplier, purchase date, quantity
   - Storing single cost in design is oversimplification

3. **ERP Integration**
   - ERP system (SAP) should be source of truth for costs
   - Design system should reference ERP item numbers
   - Costs should be queried from ERP, not stored locally

**What Should Happen:**

**Option 1:** Remove cost fields entirely, query from ERP when needed

**Option 2:** Create separate costing model

```python
# engineering/models/costing.py or finance/models/costing.py
class DesignCost(models.Model):
    """Cost tracking for designs - time-based"""

    bit_design_revision = models.ForeignKey('inventory.BitDesignRevision', ...)
    effective_date = models.DateField()
    cost_type = models.CharField(max_length=20)  # STANDARD/ACTUAL/BUDGETED
    cost_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    cost_basis = models.CharField(max_length=50)  # LAST_PO/VENDOR_QUOTE/ENGINEERING_ESTIMATE
    notes = models.TextField(blank=True)
```

---

### ⚠️ ISSUE #4: COST FIELDS IN BOM HEADER

**Model:** `inventory.BOMHeader`

**Problematic Fields:**

```python
estimated_labor_hours = models.DecimalField(max_digits=10, decimal_places=2, ...)
estimated_material_cost = models.DecimalField(max_digits=12, decimal_places=2, ...)
total_material_cost = models.DecimalField(max_digits=12, decimal_places=2, ...)
```

**Why This is Wrong:**

1. **BOM ≠ Costing**
   - BOM defines "what parts are needed" (engineering)
   - Costing calculates "how much it costs" (finance)
   - These are separate concerns

2. **Cost Calculation**
   - Material cost = Sum(BOMLine.quantity * Item.standard_cost)
   - This should be calculated, not stored
   - Storing creates data synchronization issues

3. **Labor Estimation**
   - Labor hours belong to routing/work center definitions
   - BOM shouldn't contain labor estimates
   - Production routing handles labor

**What Should Happen:**

1. **Remove cost fields from BOMHeader**
2. **Create BOM Costing Service**

```python
# engineering/services/bom_costing.py or finance/services/costing.py
class BOMCostingService:
    """Calculate BOM costs dynamically"""

    @staticmethod
    def calculate_bom_cost(bom_header, cost_date=None):
        """Calculate total BOM cost"""
        material_cost = 0
        for line in bom_header.lines.all():
            item_cost = line.component_item.get_standard_cost(cost_date)
            material_cost += line.quantity_required * item_cost

        return {
            'material_cost': material_cost,
            'calculated_at': timezone.now(),
            'cost_date': cost_date or date.today()
        }
```

---

### ⚠️ ISSUE #5: COST FIELD IN BOM LINE

**Model:** `inventory.BOMLine`

**Problematic Field:**

```python
unit_cost = models.DecimalField(max_digits=12, decimal_places=2, ...)
```

**Why This is Wrong:**

- BOMLine.unit_cost should reference Item.standard_cost
- Storing cost in BOMLine creates duplicate data
- When Item cost updates, BOMLine cost becomes stale

**What Should Happen:**

Remove `unit_cost` field, calculate dynamically:

```python
class BOMLine(models.Model):
    # ... other fields ...

    @property
    def unit_cost(self):
        """Get current unit cost from Item"""
        return self.component_item.standard_cost

    @property
    def line_cost(self):
        """Calculate total line cost"""
        return self.quantity_required * self.unit_cost
```

---

### ⚠️ ISSUE #6: ROLLER CONE COMPONENT COST

**Model:** `inventory.RollerConeComponent`

**Issue:** Contains `unit_cost` field + should be in engineering app

**Fix:** Move to engineering app + remove cost field (use Item.standard_cost instead)

---

### 📋 SUMMARY OF MISPLACED RESPONSIBILITIES

| Model | Current Location | Should Be In | Issues |
|-------|------------------|--------------|--------|
| BitDesign* | inventory | engineering | Wrong domain ownership |
| BOMHeader/Line | inventory | engineering | Wrong domain + cost fields |
| RollerCone* | inventory | engineering | Wrong domain + cost fields |
| NCR cost fields | quality | finance/core | Violates SOD, SOX compliance |
| BitDesignRevision costs | inventory | Remove or finance | Design shouldn't have cost |
| BOMHeader costs | inventory | Remove | Should calculate, not store |
| BOMLine cost | inventory | Remove | Duplicate of Item cost |
| RollerConeComponent cost | inventory | Remove | Duplicate of Item cost |

**Priority Fixes:**

1. **HIGH:** Move BOM/Design to engineering app (affects architecture)
2. **HIGH:** Remove financial fields from NCR (compliance risk)
3. **MEDIUM:** Clean up cost duplication in BOM/design models
4. **LOW:** Centralize costing logic in service layer

---

## 4. Critical Views and Forms

### 4.1 Bit Design Views

**File:** `floor_app/operations/inventory/views.py`

| View Class | Lines | Purpose | Should Move To |
|------------|-------|---------|----------------|
| BitDesignListView | 158-184 | List all bit designs | engineering/views.py |
| BitDesignDetailView | 185-195 | Design detail | engineering/views.py |
| BitDesignCreateView | 246-263 | Create new design | engineering/views.py |
| BitDesignUpdateView | 264-283 | Update design | engineering/views.py |
| BitDesignRevisionListView | 196-232 | List MAT revisions | engineering/views.py |
| BitDesignRevisionDetailView | 233-245 | MAT detail | engineering/views.py |
| BitDesignRevisionCreateView | 284-301 | Create MAT | engineering/views.py |
| BitDesignRevisionUpdateView | 302-320 | Update MAT | engineering/views.py |

**Forms:** `floor_app/operations/inventory/forms.py`
- BitDesignForm (not extracted, but exists)
- BitDesignRevisionForm (not extracted, but exists)

**Tests:** `floor_app/operations/inventory/tests/test_bitdesign_crud.py`
- TestBitDesignCreateView (Line 195)
- TestBitDesignUpdateView (Line 263)
- TestBitDesignRevisionCreateView (Line 315)
- TestBitDesignRevisionUpdateView (Line 388)

---

### 4.2 BOM Views

**File:** `floor_app/operations/inventory/views.py`

| View Class | Lines | Purpose | Should Move To |
|------------|-------|---------|----------------|
| BOMListView | 644-677 | List all BOMs | engineering/views.py |
| BOMDetailView | 678-690 | BOM detail | engineering/views.py |
| BOMCreateView | 691-702 | Create BOM | engineering/views.py |
| BOMUpdateView | 703-710 | Update BOM | engineering/views.py |

**Forms:** `floor_app/operations/inventory/forms.py`
- BOMHeaderForm (Line 74)
- BOMLineFormSet (not extracted, but likely exists)

**API Views:** `floor_app/operations/inventory/api/views.py`
- CutterBOMGridViewSet (Line 55) - Cutter BOM grid management
- CutterBOMGridValidationViewSet (Line 552) - BOM validation

---

### 4.3 NCR Views (With Financial Fields)

**File:** `floor_app/operations/quality/views.py` (not extracted, but would exist)

**Expected Views:**
- NCRListView - List all NCRs
- NCRDetailView - NCR detail (shows financial fields ⚠️)
- NCRCreateView - Create NCR (includes financial fields ⚠️)
- NCRUpdateView - Update NCR (includes financial fields ⚠️)

**Forms:** `floor_app/operations/quality/forms.py` (not extracted)

**Expected Forms:**
- NCRForm - Includes estimated_cost_impact, actual_cost_impact, lost_revenue ⚠️
- NCRDispositionForm
- RootCauseAnalysisForm
- CorrectiveActionForm

**What Needs to Change:**
1. Remove cost fields from NCRForm
2. Create separate NCRFinancialImpactForm (finance access only)
3. Update NCRDetailView to show financial data from separate model
4. Add financial approval workflow

---

### 4.4 Item/Inventory Views

**File:** `floor_app/operations/inventory/views.py`

**Key Views (not extracted, but would include):**
- ItemListView
- ItemDetailView
- ItemCreateView (includes standard_cost field - acceptable)
- SerialUnitListView
- SerialUnitDetailView
- StockListView

**Forms:** `floor_app/operations/inventory/forms.py`
- ItemForm (includes standard_cost - acceptable for inventory valuation)
- SerialUnitForm

---

### 4.5 Job Card Views

**File:** `floor_app/operations/production/views.py` (not extracted)

**Expected Views:**
- JobCardListView
- JobCardDetailView (shows estimated_cost, actual_cost, quoted_price)
- JobCardCreateView
- JobCardEvaluationView
- JobCardRoutingView

**Forms:** `floor_app/operations/production/forms.py` (not extracted)
- JobCardForm (includes cost fields - may be acceptable for production costing)
- CutterEvaluationForm

---

### 4.6 URL Mappings

**Inventory URLs:** `floor_app/operations/inventory/urls.py`

```python
# Current URLs (should move to engineering app)
path('bit-designs/', BitDesignListView.as_view(), name='bitdesign_list'),
path('bit-designs/<int:pk>/', BitDesignDetailView.as_view(), name='bitdesign_detail'),
path('bit-designs/create/', BitDesignCreateView.as_view(), name='bitdesign_create'),
path('bit-designs/<int:pk>/edit/', BitDesignUpdateView.as_view(), name='bitdesign_edit'),

path('mat/', BitDesignRevisionListView.as_view(), name='mat_list'),
path('mat/<int:pk>/', BitDesignRevisionDetailView.as_view(), name='mat_detail'),
path('mat/create/', BitDesignRevisionCreateView.as_view(), name='mat_create'),
path('mat/<int:pk>/edit/', BitDesignRevisionUpdateView.as_view(), name='mat_edit'),

path('boms/', BOMListView.as_view(), name='bom_list'),
path('boms/<int:pk>/', BOMDetailView.as_view(), name='bom_detail'),
path('boms/create/', BOMCreateView.as_view(), name='bom_create'),
path('boms/<int:pk>/edit/', BOMUpdateView.as_view(), name='bom_edit'),
```

**Should Become:**

```python
# engineering/urls.py
path('designs/', BitDesignListView.as_view(), name='design_list'),
path('designs/<int:pk>/', BitDesignDetailView.as_view(), name='design_detail'),
path('mat/', MATListView.as_view(), name='mat_list'),
path('bom/', BOMListView.as_view(), name='bom_list'),
```

---

## 5. Department Ownership Mapping

See attached CSV file: `model_ownership_mapping.csv`

### Ownership Summary by Department

| Department | Model Count | Key Models |
|------------|-------------|------------|
| **Engineering** | 9 | BitDesign*, BOM*, RollerCone* |
| **Inventory** | 26 | Item, Stock, Location, SerialUnit |
| **Production** | 19 | JobCard, BatchOrder, Routing, Evaluation |
| **Quality** | 8 | NCR, CAPA, Calibration, Disposition |
| **HR** | 15+ | Employee, Department, Training, Attendance |
| **Finance** | 12 | CostCenter, Currency, ExchangeRate, NCRFinancialImpact |
| **Purchasing** | 13 | PO, Supplier, Receipt, Invoice |
| **Sales** | 5 | Customer, Orders, Drilling, DullGrade |
| **Maintenance** | 6 | Asset, WorkOrder, PM, Downtime |
| **Planning** | 6 | Schedule, Resource, Requirements |
| **Knowledge** | 7 | Article, Document, FAQ, Training |
| **Analytics** | 4 | Event, AutomationRule, Tracking |
| **Operations** | 5 | QRCode, Address, Notification |

---

## 6. Recommendations

### Phase 1: Immediate (Critical)

1. **Create Engineering App** (Priority: HIGH)
   - Create `floor_app/operations/engineering/` app
   - Move BitDesign*, BOM*, RollerCone* models
   - Update all imports across codebase
   - Move views, forms, admin, tests
   - Update URL routing
   - **Estimated Effort:** 3-5 days

2. **Remove Financial Fields from NCR** (Priority: HIGH - Compliance)
   - Create `NCRFinancialImpact` model in core or finance app
   - Write data migration to preserve existing cost data
   - Remove cost fields from `NonconformanceReport`
   - Update views/forms
   - Implement separate financial approval workflow
   - **Estimated Effort:** 2-3 days

### Phase 2: Cleanup (Medium Priority)

3. **Remove Cost Duplication in Design/BOM**
   - Remove `standard_cost`, `last_purchase_cost` from BitDesignRevision
   - Remove cost fields from BOMHeader
   - Remove `unit_cost` from BOMLine (calculate from Item)
   - Create BOM costing service for calculations
   - **Estimated Effort:** 2-3 days

4. **Centralize Costing Logic**
   - Create `CostingService` class
   - Implement dynamic cost calculations
   - Remove stored costs where appropriate
   - **Estimated Effort:** 3-4 days

### Phase 3: Documentation & Standards

5. **Document Module Responsibilities**
   - Create architecture decision records (ADRs)
   - Document which module owns which domain
   - Create data flow diagrams
   - **Estimated Effort:** 2 days

6. **Establish Coding Standards**
   - Define rules for cross-module references
   - Establish when to use ForeignKey vs BigIntegerField
   - Document approval workflows
   - **Estimated Effort:** 1 day

### Total Estimated Effort: 15-20 days

---

## Appendix: Model Statistics

- **Total Apps:** 32
- **Total Models:** ~150+ (estimated)
- **Models with Foreign Keys:** ~120
- **Models with Cost/Price Fields:** 10+
- **Models Using AuditMixin:** ~100
- **Models Using SoftDeleteMixin:** ~80
- **Models Using PublicIdMixin:** ~60

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20
**Contact:** Floor Management System Team

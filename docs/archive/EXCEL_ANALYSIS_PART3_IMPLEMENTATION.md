## Integration Points and Dependencies

### Inter-Workbook Dependencies

1. **Job Card ↔ Bits Tracking**
   - **Current:** Manual duplication - same bit info entered in both
   - **Needed:** Job card pulls bit history from tracking DB, updates tracking DB on completion

2. **Job Card ↔ Cutter Inventory**
   - **Current:** Job card calculates cutter needs, user manually creates transactions in inventory workbook
   - **Needed:** Job card quotation approval triggers automatic inventory transactions (subtract consumed cutters)

3. **Bits Tracking ↔ Cutter Inventory (BOM Requirements)**
   - **Current:** L3&L4 BOMs sheet manually maintained, cross-references tracking
   - **Needed:** Real-time query of active repair jobs → BOM lookup → cutter requirements aggregation

4. **PO Tracking ↔ Cutter Inventory**
   - **Current:** When PO received, user manually creates addition transaction
   - **Needed:** PO GRN posting triggers automatic inventory transaction

5. **ERP ↔ All Workbooks**
   - **Current:** Manual export/import, reconciliation spreadsheet
   - **Needed:** API integration or scheduled sync (bi-directional)

---

## Sample Data Patterns

### Representative Bit Data

**New Bit (First Evaluation):**
```
base_serial_number: 14204328
size: 8.5"
type: GT65RHs
original_mat_number: 1267829M
customer: LSTK
repair_revision: 0
work_order_number: 2025-ARDT-LV4-015
date_received: 2025-01-16
source_location: ARDT-LV4
disposition: Rerun
```

**First Repair:**
```
base_serial_number: 12721812
repair_revision: 1
work_order_number: 2025-ARDT-LV4-023
date_received: 2025-02-01
source_location: LSTK
disposition: Repair
```

**Second Repair:**
```
base_serial_number: 12721812
repair_revision: 2
work_order_number: 2025-ARDT-LV4-047
date_received: 2025-04-15
source_location: LSTK
disposition: Scrap (too many damaged cutters)
```

### Representative Evaluation Data

**Evaluation Symbols:**
```
blade_1_pocket_1: X (replace)
blade_1_pocket_2: X (replace)
blade_1_pocket_3: O (okay)
blade_1_pocket_4: O (okay)
blade_1_pocket_5: R (rotate)
blade_1_pocket_6: X (replace)
blade_1_pocket_7: P (pocket build-up needed)
blade_1_pocket_8: O (okay)
blade_2_pocket_1: X (replace)
blade_2_pocket_2: L (lost cutter)
... (continues for all blades and pockets)
```

**Summary Counts:**
```
total_x: 47 (47 cutters to replace)
total_o: 103 (103 cutters okay)
total_r: 8 (8 cutters to rotate)
total_l: 2 (2 cutters lost)
total_p: 3 (3 pockets need build-up)
```

### Representative Cutter Data

**Cutter Master:**
```
sap_number: 802065
type: Round
size: 1313
grade: CT97
chamfer: 0.010"
category: P-Premium
is_obsolete: false
replacement_cutter_id: null
```

**Inventory Snapshot (as of 2025-11-09):**
```
sap_number: 802065
eno_as_new: 12
eno_ground: 8
ardt_reclaim: 24
lstk_reclaim: 6
new_stock: 145
total_available: 195
six_month_consumption: 240
two_month_consumption: 80
safety_stock: 85
bom_requirement: 67
on_order: 100
forecast: 195 - 67 + 100 = 228 (OK)
```

**Cutter Transaction Log Sample:**
```
2025-01-10 | 802065 | PO-2025-003 received | New Stock | Addition: 100
2025-01-15 | 802065 | Job 2025-ARDT-LV4-015 | New Stock | Subtraction: 8
2025-01-20 | 802065 | Reclaimed from 13824396 | ENO As New | Addition: 6
2025-01-25 | 802065 | Ground ENO cutters | ENO As New | Subtraction: 10
2025-01-25 | 802065 | Ground ENO cutters | ENO Ground | Addition: 10
```

### Representative Quotation Data

**Quotation Breakdown:**
```
work_order_number: 2025-ARDT-LV4-015
customer: LSTK

Cutter Line Items:
  - 802065 (CT97 1313 0.010") × 8 @ $45.00 = $360.00
  - 179692 (ELITE RC 1313 0.018") × 12 @ $52.00 = $624.00
  - 467367 (CT36 1613 0.018") × 6 @ $58.00 = $348.00
  ... (more cutters)
  Subtotal Cutters: $2,450.00

Labor Line Items:
  - Evaluation (2 hrs @ $35/hr) = $70.00
  - De-brazing (4 hrs @ $40/hr) = $160.00
  - Cutter replacement (8 hrs @ $45/hr) = $360.00
  - Brazing (6 hrs @ $50/hr) = $300.00
  - QC inspection (2 hrs @ $35/hr) = $70.00
  Subtotal Labor: $960.00

Material Line Items:
  - Brazing alloy = $120.00
  - Consumables = $85.00
  Subtotal Material: $205.00

Subtotal: $3,615.00
Overhead (15%): $542.25
Margin (20%): $831.45
Total: $4,988.70
```

---

## Implementation Prompt

---

# IMPLEMENTATION PROMPT: Rebuilding Excel Logic in Django + PostgreSQL

## Executive Summary

You are tasked with implementing a **PDC Bit Manufacturing & Repair Management System** as a Django web application with PostgreSQL database. This system replaces 6 Excel workbooks (87 sheets, millions of rows) currently used to manage:

1. **Bit Repair Job Cards** - Comprehensive evaluation, quotation, and repair workflow for individual PDC drilling bits
2. **Bit Lifecycle Tracking** - Master registry of all bits across customers and repair cycles
3. **Cutter Inventory Management** - Real-time availability forecasting with multiple ownership categories
4. **Purchase Order Tracking** - Cutter and consumable procurement lifecycle
5. **Consumables Catalog** - ERP-ready spare parts and consumables catalog
6. **ERP Reconciliation** - Inventory variance detection and correction

The Excel analysis above documents how these workbooks currently function. Your goal is to **preserve all business value** while **eliminating Excel's limitations** through proper database design, modern web UIs, and automated workflows.

---

## Guiding Principles

1. **Do NOT blindly copy Excel structure** - Excel uses workarounds (wide grids, formulas, named ranges) due to its limitations. Design proper normalized database.

2. **Preserve business logic** - Understand WHAT the Excel does (business rules) and WHY, then implement cleanly in code.

3. **Improve on Excel** - Add features Excel can't do: concurrent editing, audit trails, search/filter, alerts, workflows, validation.

4. **Migration-friendly** - Design import tools to load historical data from Excel without losing history.

5. **User-familiar** - UI should feel intuitive to users familiar with Excel, but better (e.g., Handsontable grid for cutter evaluation).

---

## Module Breakdown

### Module 1: Bit & Repair Job Management

**Purpose:** Track bits and their repair/evaluation jobs (replaces Bits Tracking workbook + Job Card Data sheet)

**Models:**

1. **`Bit`** (formerly scattered across workbooks)
   - `base_serial_number` (unique, indexed)
   - `size`, `type`
   - `original_mat_design` (FK)
   - `customer` (FK)
   - `date_manufactured`
   - `current_status`
   - Audit fields

2. **`BitRepairJob`** (one row per repair/evaluation)
   - `bit` (FK)
   - `repair_revision` (0 for new, 1+ for repairs)
   - Unique constraint: (bit_id, repair_revision)
   - `work_order_number` (unique, auto-generated: `YYYY-SOURCE-LV#-###`)
   - `date_received`, `source_location`
   - `mat_design` (FK - can differ from original if redesigned)
   - `disposition` (Repair, Scrap, Rerun)
   - `evaluated_by`, `qc_by`, `reviewed_by`, `approved_by` (FK to User)
   - Date fields for each approval stage
   - `accomplished_date`
   - `remarks`, `job_name`, `issues_report`
   - `pdc_production_days` (calculated or manual)
   - ERP integration fields
   - Audit fields

3. **`BitDesign`** (MAT master)
   - `mat_number` (e.g., "1267829")
   - `revision` (e.g., "M")
   - `size`, `type`, `level` (L3/L4/L5)
   - `description`
   - `is_active`, `superseded_by` (FK to self)
   - Audit fields

**Pages/Views:**

1. **Bit List** (`/bits/`)
   - Table view: SN, Size, Type, Customer, Current Status, Last Activity
   - Filter: Customer, Size, Type, Status, Date range
   - Search: SN (autocomplete)
   - Click row → Bit Detail

2. **Bit Detail** (`/bits/<sn>/`)
   - Header: SN, Size, Type, Original MAT, Customer
   - Tabs:
     - **History:** Timeline of all repair jobs (R0, R1, R2...)
     - **Current Status:** Latest repair job details
     - **BOM:** Current design BOM and cutter map
   - Actions: "Create New Repair Job"

3. **Repair Job List** (`/repair-jobs/`)
   - Table: Work Order, SN, Customer, Date Received, Status, Days in Production
   - Filter: Customer, Status, Date range, Evaluator
   - Search: Work Order, SN
   - Click row → Repair Job Detail

4. **Repair Job Detail** (`/repair-jobs/<work_order>/`)
   - **Header:** Work Order, SN, Size, Type, MAT, Customer, Status
   - **Tabs:**
     - **Identification:** Basic info, dates, approvals
     - **Evaluation:** Cutter evaluation grid (see Module 2)
     - **Process Routing:** Process steps with operator signatures
     - **QC Checklists:** Evaluation checklist, API thread, Die check
     - **Quotation:** Cost breakdown (see Module 5)
     - **Documents:** Uploaded photos, PDFs, auto-generated forms
     - **History:** Audit log (who changed what when)
   - **Actions:** Edit, Print Evaluation Form (LSTK/ARAMCO/HAL), Print Quotation, Complete Job

**Business Logic:**

- **Auto-generate Work Order Number:** `YYYY-{source_code}-LV{level}-{sequence}` (e.g., 2025-ARDT-LV4-015)
- **Repair Revision Auto-increment:** When creating repair job for existing bit, auto-set `repair_revision = MAX(repair_revision) + 1`
- **Status Workflow:** Draft → In Evaluation → Quoted → Approved → In Repair → QC → Completed → Delivered
- **Validation:** Can't approve job without evaluation data; can't complete without QC checklist
- **Notifications:** Email evaluator when job assigned; email customer when quotation ready

---

### Module 2: Cutter Evaluation Grid

**Purpose:** Replaces Evaluation, ARDT Cutter Entry, Eng. Cutter Entry sheets

**Models:**

1. **`CutterMap`** (design-level cutter layout)
   - `bit_design` (FK)
   - `blade_number` (1-12+)
   - `pocket_number` (1-34+)
   - `cutter` (FK to Cutter)
   - `is_primary` (vs backup)
   - `color_code` (for UI grouping)
   - Unique: (bit_design, blade, pocket)

2. **`EvaluationRecord`** (job-level cutter condition)
   - `repair_job` (FK)
   - `blade_number`
   - `pocket_number`
   - `symbol` (X, O, R, S, L, V, P, I, B)
   - `remarks`
   - `created_by`, `created_at`
   - Unique: (repair_job, blade, pocket)

3. **`CutterReplacementPlan`** (ARDT vs Eng entry)
   - `repair_job` (FK)
   - `entry_type` (ARDT, Engineering)
   - `blade_number`
   - `pocket_number`
   - `action` (Replace, Rotate, BuildUp, etc.)
   - `replacement_cutter` (FK to Cutter, if different from design)
   - `created_by`, `created_at`

**Pages/Views:**

1. **Evaluation Grid** (`/repair-jobs/<work_order>/evaluation/`)
   - **Layout:** Handsontable-style grid
     - Columns: Pocket positions (1, 2, 3... up to max for this design)
     - Rows: Blade numbers (1, 2, 3... up to 12+)
     - Pre-populated: Cutter part numbers from design's CutterMap
   - **Interaction:**
     - Click cell → enter symbol (X, O, R, S, L, V, P, I, B)
     - Dropdown or keyboard shortcut
     - Right-click → Add remark
     - Color-code cells by symbol (X=red, O=green, R=yellow, etc.)
   - **Real-time summary:**
     - Count of each symbol
     - Total cutters to replace (X + L)
   - **Instructions pane:**
     - Show relevant TechnicalInstructions for this bit/MAT
   - **Save:** Auto-save on change (AJAX)

2. **Cutter Replacement Entry** (`/repair-jobs/<work_order>/cutter-replacement/`)
   - **ARDT Entry:**
     - Same grid as Evaluation
     - Mark cutters to replace (checkbox or X)
     - Summary: Quantity needed per cutter part#
   - **Engineering Override:**
     - Side-by-side: ARDT plan vs Engineering changes
     - Engineer can modify quantities, substitute cutters
     - Final plan highlighted
   - **Inventory Check:**
     - Live lookup: Is cutter in stock?
     - Warning if insufficient inventory
     - Link to create purchase requisition

**Business Logic:**

- **Load CutterMap:** On job creation, copy design's CutterMap to evaluation records (pre-populate grid)
- **Symbol Meanings:**
  - X = Replace (subtract from inventory)
  - O = Okay (no action)
  - R = Rotate (no inventory impact)
  - S, L = Replace (subtract from inventory)
  - V, P, I, B = Body work (material consumption, not cutter)
- **Quotation Trigger:** When Engineering entry saved, re-calculate quotation
- **Inventory Reservation:** Option to "reserve" cutters when job approved (soft lock, warn if another job tries to use)

---

### Module 3: Cutter Master & BOM

**Purpose:** Replaces cutter sheets in inventory workbook, BOM sheets in job card

**Models:**

1. **`Cutter`** (cutter catalog)
   - `sap_number` (unique, indexed)
   - `type`, `size`, `grade`, `chamfer`
   - `description`
   - `category` (Premium, Standard, Super Premium, etc.)
   - `unit_price` (current price)
   - `is_obsolete`
   - `replacement_cutter` (FK to Cutter)
   - Audit fields

2. **`CutterPriceHistory`** (preserve pricing over time)
   - `cutter` (FK)
   - `effective_date`
   - `unit_price`
   - `currency`
   - Unique: (cutter, effective_date)

3. **`BOM`** (bill of materials for a design)
   - `bit_design` (FK)
   - `line_number`
   - `cutter` (FK)
   - `quantity`
   - `is_primary` (vs backup/alternate)
   - `position_type` (ID, Cone, Nose, Shoulder, Gauge)
   - Audit fields

**Pages/Views:**

1. **Cutter Catalog** (`/cutters/`)
   - Table: SAP#, Type, Size, Grade, Chamfer, Category, Unit Price, Stock Status
   - Filter: Category, Type, Size, Obsolete
   - Search: SAP#, Description
   - Click row → Cutter Detail

2. **Cutter Detail** (`/cutters/<sap#>/`)
   - **Info:** SAP#, specs, category, current price
   - **Tabs:**
     - **Inventory:** Current stock by ownership category (see Module 4)
     - **Price History:** Table of price changes
     - **Usage:** Which designs use this cutter (BOM references)
     - **Transactions:** Recent additions/subtractions
     - **Replacement:** If obsolete, show replacement cutter

3. **BOM Editor** (`/bit-designs/<mat#>/bom/`)
   - **Grid view:**
     - Columns: Line#, Cutter SAP#, Description, Qty, Primary/Backup, Position Type
     - Add/Edit/Delete rows
   - **Cutter Map Editor:**
     - Visual grid (blade x pocket)
     - Assign cutter to each pocket
     - Color-code by cutter type
     - Save generates CutterMap records

**Business Logic:**

- **Price Lookup:** When creating quotation, use price effective as of quotation date (not current price)
- **Obsolescence:** If cutter marked obsolete, show warning when used in BOM; suggest replacement
- **BOM Validation:** Prevent deleting cutter if used in active BOMs (or warn and suggest replacement)

---

### Module 4: Cutter Inventory Management

**Purpose:** Replaces Cutter Inventory workbook (real-time availability, consumption tracking, forecasting)

**Models:**

1. **`CutterOwnershipCategory`** (lookup table)
   - `name` (ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock, Retrofit)
   - `priority` (for consumption order: 1=New Stock, 2=ENO As New, 3=ENO Ground, 4=Reclaim, etc.)

2. **`CutterTransaction`** (transaction log - source of truth)
   - `date`
   - `cutter` (FK)
   - `ownership_category` (FK)
   - `addition_qty`, `subtraction_qty`
   - `reference_type` (PO, RepairJob, Reclaim, Adjustment, Transfer)
   - `reference_id` (polymorphic FK)
   - `description`
   - `created_by`, `created_at`
   - Indexed: (cutter, date), (reference_type, reference_id)

3. **`CutterInventorySummary`** (materialized view or calculated model)
   - `cutter` (FK, unique)
   - `ownership_category` (FK)
   - `current_balance` (calculated from transactions)
   - `six_month_consumption` (calculated from transactions where date > today - 182 days)
   - `three_month_consumption`
   - `two_month_consumption` (= 6mo / 3)
   - `safety_stock` (calculated per tiered formula)
   - `bom_requirement` (calculated from active repair jobs' BOMs)
   - `on_order` (sum from open POs)
   - `forecast` (= current_balance - bom_requirement + on_order)
   - `status` (OK, LOW, SHORTAGE, EXCESS)
   - `last_updated` (timestamp)

**Pages/Views:**

1. **Inventory Dashboard** (`/inventory/`)
   - **Summary Cards:**
     - Total cutter types tracked
     - Cutters in shortage (forecast < safety stock)
     - Cutters in excess (forecast > 2x safety stock)
     - Total value (sum of balance × unit price)
   - **Shortage Alert Table:**
     - Cutters where forecast < safety stock
     - Columns: SAP#, Description, Current Balance, BOM Req, On Order, Forecast, Safety Stock, Shortage Qty
     - Action: "Create Purchase Requisition"

2. **Inventory Detail Table** (`/inventory/cutters/`)
   - **Table:** All cutters with inventory metrics
     - SAP#, Description, ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock, Total Balance, 6mo Consumption, Safety Stock, BOM Req, On Order, Forecast, Status
   - **Filter:** Category, Status (OK/LOW/SHORTAGE/EXCESS), Type
   - **Search:** SAP#, Description
   - **Export:** Excel, CSV
   - **Color-code rows:** Red=shortage, Yellow=low, Green=OK, Blue=excess

3. **Cutter Inventory Detail** (`/inventory/cutters/<sap#>/`)
   - **Current Stock Card:**
     - Pie chart: Stock by ownership category
     - Table: Category, Balance, % of Total
   - **Consumption Trends Chart:**
     - Line graph: Consumption per month (last 12 months)
     - Forecast line (if trend continues)
   - **Transaction Log:**
     - Table: Date, Type (Addition/Subtraction), Qty, Balance After, Reference, Created By
     - Filter: Date range, Type
     - Pagination

4. **Add Transaction** (`/inventory/cutters/<sap#>/add-transaction/`)
   - **Form:**
     - Transaction Type (Addition / Subtraction)
     - Ownership Category (dropdown)
     - Quantity
     - Reference Type (PO, Repair Job, Reclaim, Adjustment)
     - Reference ID (lookup)
     - Description
   - **Submit:** Create transaction, recalculate summary
   - **Validation:** Can't subtract more than available balance

5. **Bulk Import Transactions** (`/inventory/import/`)
   - **Upload CSV/Excel:**
     - Columns: Date, SAP#, Category, Addition, Subtraction, Reference, Description
     - Validate all rows before import
     - Show errors (invalid SAP#, negative balance, etc.)
   - **Confirm and Import:**
     - Create transactions in batch
     - Recalculate summaries

**Business Logic:**

- **Auto-Create Transactions:**
  - When repair job approved → subtract cutters (reference_type=RepairJob, reference_id=job.id)
  - When PO GRN posted → add cutters (reference_type=PO, reference_id=po_line.id)
  - When bit de-brazed → add reclaimed cutters (reference_type=Reclaim, reference_id=job.id)
- **Safety Stock Calculation:** Implement tiered formula from Excel (if consumption >= 300, add 10; elif >= 200, add 5; ...)
- **BOM Requirement Aggregation:** Query all repair jobs with status in ("In Evaluation", "Quoted", "Approved", "In Repair") → join to BOM → sum cutter quantities
- **Consumption Calculation:**
  - 6-month: `SUM(subtraction_qty) WHERE cutter_id = X AND date > today - 182 days`
  - Use Django ORM aggregation or raw SQL
- **Summary Refresh:**
  - Option 1: Trigger on transaction create/update → recalculate summary
  - Option 2: Celery task runs every hour → recalculate all summaries
  - Option 3: Calculate on-the-fly (query transactions live) - only if transaction volume low
- **Alerts:**
  - Email notification when cutter goes into shortage
  - Dashboard badge showing count of shortage cutters

---

### Module 5: Quotation & Pricing

**Purpose:** Replaces Quotation sheet in job card

**Models:**

1. **`Quotation`**
   - `repair_job` (FK, unique)
   - `quotation_date`
   - `customer` (FK)
   - `total_cutter_cost` (calculated)
   - `total_labor_cost` (calculated)
   - `total_material_cost` (calculated)
   - `overhead_rate` (%, e.g., 15.0)
   - `margin_rate` (%, e.g., 20.0)
   - `total_amount` (calculated)
   - `status` (Draft, Sent, Approved, Rejected)
   - `approved_date`, `approved_by`
   - Audit fields

2. **`QuotationLine`**
   - `quotation` (FK)
   - `line_number`
   - `line_type` (Cutter, Labor, Material)
   - `description`
   - `cutter` (FK, if line_type=Cutter)
   - `quantity`
   - `unit_price`
   - `line_amount` (= quantity × unit_price)

3. **`LaborRateHistory`**
   - `process_step_type` (Evaluation, De-brazing, Cutter Replacement, Brazing, QC, etc.)
   - `effective_date`
   - `hourly_rate`
   - `currency`
   - Unique: (process_step_type, effective_date)

**Pages/Views:**

1. **Quotation Detail** (`/repair-jobs/<work_order>/quotation/`)
   - **Header:** Work Order, Customer, Quotation Date, Status
   - **Line Items Table:**
     - Grouped by type (Cutters, Labor, Materials)
     - Columns: Description, Qty, Unit Price, Line Amount
     - Subtotals per group
   - **Summary:**
     - Subtotal Cutters: $X
     - Subtotal Labor: $Y
     - Subtotal Materials: $Z
     - Overhead (15%): $A
     - Margin (20%): $B
     - **Total: $C**
   - **Actions:**
     - Recalculate (refresh based on current cutter plan, labor estimates)
     - Edit Overhead/Margin Rates
     - Send to Customer (email PDF)
     - Mark as Approved/Rejected

2. **Quotation Editor** (`/repair-jobs/<work_order>/quotation/edit/`)
   - **Auto-populate from:**
     - Cutter Replacement Plan (Engineering or ARDT)
     - Labor estimates (editable)
     - Material estimates (editable)
   - **Manual adjustments:**
     - Add/remove lines
     - Override unit prices
     - Adjust quantities
   - **Save:** Recalculate totals

3. **Print Quotation** (`/repair-jobs/<work_order>/quotation/print/`)
   - **PDF template:**
     - Company letterhead
     - Customer info
     - Job details (SN, Size, Type)
     - Line items table
     - Total in large font
     - Terms and conditions
     - Signature block

**Business Logic:**

- **Auto-Generate on Engineering Approval:**
  - When CutterReplacementPlan (Engineering) saved → create/update Quotation
  - Create QuotationLine per cutter × qty
  - Look up cutter price effective as of quotation_date
- **Labor Estimation:**
  - Estimate hours per process step based on bit size/type
  - OR user manually enters hours
  - Look up labor rate effective as of quotation_date
  - Create QuotationLine per labor step
- **Material Estimation:**
  - Estimate consumables (brazing alloy, etc.) based on cutter count, body work
  - OR user manually enters
- **Totals Calculation:**
  ```python
  subtotal = sum(line.line_amount for line in quotation.lines.all())
  overhead_amount = subtotal * (quotation.overhead_rate / 100)
  subtotal_with_overhead = subtotal + overhead_amount
  margin_amount = subtotal_with_overhead * (quotation.margin_rate / 100)
  total = subtotal_with_overhead + margin_amount
  ```
- **Approval Workflow:**
  - Status: Draft → Sent (email to customer) → Approved (customer confirms) → OR Rejected
  - If Approved → repair job status advances to "In Repair"
  - Trigger inventory transactions on approval

---

### Module 6: Purchase Order Management

**Purpose:** Replaces PO Customs workbook

**Models:**

1. **`Supplier`**
   - `name`
   - `contact_info` (JSON or separate contact model)
   - `is_active`
   - Audit fields

2. **`PurchaseOrder`**
   - `po_number` (unique)
   - `po_date`
   - `supplier` (FK)
   - `status` (Draft, Sent, In Transit, Customs, Received, Closed)
   - `expected_delivery_date`
   - `total_amount` (calculated)
   - Audit fields

3. **`PurchaseOrderLine`**
   - `purchase_order` (FK)
   - `line_number`
   - `item_type` (Cutter, Consumable)
   - `cutter` (FK, if item_type=Cutter)
   - `consumable` (FK, if item_type=Consumable)
   - `description`
   - `ordered_qty`
   - `received_qty`
   - `unit_price`
   - `line_amount`

4. **`POShipment`** (tracking shipping/customs)
   - `purchase_order` (FK)
   - `awb_number` (air waybill)
   - `shipping_date`
   - `eta_date`
   - `clearance_eta_date`
   - `received_date`
   - `grn_number` (goods receipt note)
   - `erp_grn_number`

**Pages/Views:**

1. **PO List** (`/purchasing/pos/`)
   - Table: PO#, Date, Supplier, Status, Total Amount, Expected Delivery, Received Date
   - Filter: Supplier, Status, Date range
   - Search: PO#
   - Actions: Create New PO

2. **PO Detail** (`/purchasing/pos/<po#>/`)
   - **Header:** PO#, Supplier, Date, Status, Total
   - **Line Items Table:** Item, Description, Ordered Qty, Received Qty, Unit Price, Amount
   - **Shipment Tracking:**
     - AWB#, Shipping Date, ETA, Clearance ETA, Received Date, GRN#
   - **Actions:**
     - Edit (if status=Draft)
     - Send to Supplier (email, change status to Sent)
     - Update Shipment (add AWB, dates)
     - Receive (open GRN form)

3. **Create PO** (`/purchasing/pos/create/`)
   - **Form:**
     - Supplier (dropdown)
     - PO Date (auto = today)
     - Expected Delivery Date
     - **Line Items (dynamic formset):**
       - Item Type (Cutter / Consumable)
       - Item (lookup, filtered by type)
       - Description (auto-filled)
       - Qty
       - Unit Price
       - Add/Remove Line
   - **Submit:** Create PO, status=Draft

4. **Receive PO** (`/purchasing/pos/<po#>/receive/`)
   - **GRN Form:**
     - Received Date (default = today)
     - GRN Number (auto-generated or manual)
     - **Line Items:**
       - Show ordered qty vs previously received
       - Enter qty received (this shipment)
       - Checkbox: "Fully received"
     - **Submit:** Create GRN, update PO line received_qty
       - If all lines fully received → PO status = Closed
       - Create inventory transactions (add to cutter/consumable inventory)

**Business Logic:**

- **Auto-generate PO Number:** `PO-YYYY-###` (year + sequence)
- **Auto-generate GRN Number:** `GRN-YYYY-###`
- **Partial Receipts:** Allow receiving PO in multiple shipments (sum received_qty per line)
- **Inventory Transaction:** On GRN posting, create CutterTransaction (if cutter) or ConsumableTransaction (if consumable)
  - addition_qty = received_qty
  - reference_type = "PO", reference_id = po_line.id
- **Update "On Order" in Inventory:** Query open PO lines for each cutter → sum ordered_qty - received_qty
- **Email Notifications:** Send PO PDF to supplier on "Send to Supplier" action

---

### Module 7: Process Routing & QC Checklists

**Purpose:** Replaces Router Sheet, E Checklist, API Thread Inspection, Die Check sheets

**Models:**

1. **`ProcessStepDefinition`** (template)
   - `step_number`
   - `description` (Nozzle Removal, Washing, Sand Blasting, etc.)
   - `is_required`
   - `typical_duration_hours`

2. **`ProcessStep`** (instance per job)
   - `repair_job` (FK)
   - `step_definition` (FK)
   - `completed_date`
   - `completed_time`
   - `operator` (FK to User)
   - `remarks`

3. **`QCChecklistDefinition`** (template)
   - `checklist_type` (Evaluation, API Thread, Die Check)
   - `item_number`
   - `item_description`

4. **`QCChecklistItem`** (instance per job)
   - `repair_job` (FK)
   - `checklist_definition` (FK)
   - `result` (OK, Not OK, N/A)
   - `remarks`
   - `checked_by` (FK to User)
   - `checked_date`

**Pages/Views:**

1. **Process Routing** (`/repair-jobs/<work_order>/routing/`)
   - **Table:** Step #, Description, Date, Time, Operator, Remarks, Status
   - **Status per step:** Pending, In Progress, Completed
   - **Actions:**
     - Mark step as In Progress (operator signs in)
     - Mark step as Completed (operator signs off, enter date/time)
     - Add Remark

2. **QC Checklist** (`/repair-jobs/<work_order>/qc/<type>/`)
   - **Type:** Evaluation Checklist / API Thread Inspection / Die Check
   - **Table:** Item #, Description, OK, Not OK, N/A, Remarks
   - **Radio buttons:** OK / Not OK / N/A per item
   - **Textarea:** Remarks per item
   - **Save:** Update QCChecklistItem records
   - **Completion status:** "X of Y items checked"

3. **Print Router Sheet** (`/repair-jobs/<work_order>/routing/print/`)
   - **PDF:** Formatted router sheet for floor use (operators can print and carry with bit)

**Business Logic:**

- **Auto-create ProcessSteps:** When repair job created, copy all ProcessStepDefinitions to ProcessStep instances
- **Auto-create QCChecklistItems:** When repair job enters "QC" status, copy checklist definitions
- **Validation:** Can't mark job as Completed unless all required process steps completed and all QC checklists 100% checked
- **Operator Signature:** Electronic signature via User login (no wet signature needed; audit trail shows who/when)

---

### Module 8: Technical Instructions & Lookup Tables

**Purpose:** Replaces Instructions sheet

**Models:**

1. **`TechnicalInstruction`**
   - `title`
   - `applies_to_type` (SerialNumber, MATNumber, BitType, BitSize, Customer, All)
   - `applies_to_value` (e.g., "14081145", "1267829M", "GT65RHs", "8.5", "ARAMCO", "*")
   - `instruction_text` (rich text)
   - `is_active`
   - `priority` (higher priority shown first)
   - Audit fields

**Pages/Views:**

1. **Instructions List** (`/instructions/`)
   - Table: Title, Applies To, Instruction (truncated), Active
   - Filter: Applies To Type, Active
   - Search: Title, Instruction text
   - Actions: Add Instruction, Edit, Deactivate

2. **Instruction Editor** (`/instructions/<id>/edit/`)
   - Form: Title, Applies To Type (dropdown), Applies To Value, Instruction (WYSIWYG editor), Active
   - Save

3. **Relevant Instructions Widget** (embedded in Repair Job pages)
   - Query instructions WHERE:
     - applies_to_type = "SerialNumber" AND applies_to_value = job.bit.base_serial_number
     - OR applies_to_type = "MATNumber" AND applies_to_value = job.mat_design.mat_number
     - OR applies_to_type = "BitType" AND applies_to_value = job.bit.type
     - OR applies_to_type = "Customer" AND applies_to_value = job.bit.customer.name
     - OR applies_to_type = "All"
   - Display in sidebar or collapsible panel
   - Order by priority DESC

**Business Logic:**

- **Lookup on Page Load:** When user opens repair job detail, run query to find matching instructions
- **Highlight Special Instructions:** If instruction marked as "Critical", show in red/bold

---

### Module 9: Consumables Catalog

**Purpose:** Replaces Consumables workbook

**Models:**

1. **`Consumable`**
   - `item_number` (unique, e.g., "FS-0678", "CN-000208")
   - `product_name` (ERP-recognized name)
   - `search_name` (common name)
   - `product_type` (Item, Service)
   - `product_subtype` (Product, Product Master)
   - `item_group`
   - `inventory_unit` (EA, Kilogram, Liter, etc.)
   - `item_model_group` (PhyInv, etc.)
   - `storage_dimension_group` (SWL, etc.)
   - `tracking_dimension_group`
   - `configurations` (JSON or separate model for product variants)
   - `quarterly_consumption`
   - `minimum_buffer_stock`
   - `image_url`
   - `source` (supplier)
   - Audit fields

2. **`ConsumableTransaction`** (similar to CutterTransaction)
   - `date`
   - `consumable` (FK)
   - `addition_qty`, `subtraction_qty`
   - `reference_type`, `reference_id`
   - `description`
   - `created_by`, `created_at`

**Pages/Views:**

1. **Consumables Catalog** (`/consumables/`)
   - Table: Item#, Product Name, Search Name, Type, Unit, Quarterly Consumption, Min Buffer Stock, Current Balance
   - Filter: Type, Item Group
   - Search: Item#, Name
   - Actions: Add Consumable

2. **Consumable Detail** (`/consumables/<item#>/`)
   - Info: Item#, names, specs, image
   - Current Balance
   - Transaction Log (similar to cutter transactions)

**Business Logic:**

- **ERP Export:** Provide CSV/Excel export formatted for Microsoft Dynamics import
- **Inventory Tracking:** Similar to cutters - track additions (POs) and subtractions (repair jobs, general use)

---

### Module 10: Reporting & Analytics

**Purpose:** Dashboards and reports (Excel provides limited reporting)

**Pages/Views:**

1. **Main Dashboard** (`/dashboard/`)
   - **KPI Cards:**
     - Bits in house (count by status)
     - Avg. production days (last 30 days)
     - Cutters in shortage (count)
     - Open quotations (count)
   - **Charts:**
     - Bits received per month (bar chart)
     - Bits by disposition (pie chart: Repair, Scrap, Rerun)
     - Cutter consumption trends (line chart)
     - Top 10 cutters by consumption
   - **Recent Activity:**
     - Latest repair jobs created
     - Latest quotations sent
     - Latest POs received

2. **Bits Report** (`/reports/bits/`)
   - **Filters:** Date range, Customer, Size, Type, Status, Disposition
   - **Columns:** Work Order, SN, Size, Type, Customer, Date Received, Disposition, Accomplished Date, Days in Production
   - **Aggregations:** Count, Avg Days, Sum Quotation Amounts
   - **Export:** Excel, CSV, PDF

3. **Cutter Consumption Report** (`/reports/cutter-consumption/`)
   - **Filters:** Date range, Cutter Category, Customer (consumed for which customer's jobs)
   - **Columns:** Cutter SAP#, Description, Qty Consumed, Total Cost, Jobs (count)
   - **Aggregations:** Total Qty, Total Cost
   - **Export:** Excel, CSV

4. **Financial Report** (`/reports/financial/`)
   - **Filters:** Date range, Customer
   - **Columns:** Work Order, SN, Customer, Quotation Amount, Status (Approved/Rejected), Approval Date
   - **Aggregations:** Total Quoted, Total Approved, Approval Rate (%)
   - **Export:** Excel, PDF

5. **Operator Performance Report** (`/reports/operators/`)
   - **Filters:** Date range, Operator
   - **Columns:** Operator, Process Step, Jobs Completed (count), Avg Time per Step, Total Hours
   - **Export:** Excel, CSV

**Business Logic:**

- **Report Generation:** Django ORM queries with aggregation
- **Caching:** Cache complex reports (refresh hourly or on-demand)
- **Scheduled Reports:** Celery task to email weekly summary to management

---

### Module 11: User Management & Permissions

**Purpose:** Role-based access control (Excel has no permissions)

**Roles:**

1. **Administrator** - Full access
2. **Manager** - View all, edit all, approve quotations
3. **Evaluator** - Create/edit repair jobs, enter evaluations
4. **Engineer** - Review evaluations, override cutter plans, approve quotations
5. **Operator** - Sign off process steps, view assigned jobs
6. **QC Inspector** - Complete QC checklists
7. **Inventory Clerk** - Manage cutter/consumable inventory, enter transactions, manage POs
8. **Viewer** - Read-only access to reports

**Permissions:**

- Django's built-in `auth` system + `django-guardian` for object-level permissions
- Permissions: `view_repairjob`, `add_repairjob`, `change_repairjob`, `delete_repairjob`, `approve_quotation`, `manage_inventory`, etc.

**Pages/Views:**

1. **User Management** (`/admin/users/`)
   - Use Django admin or custom UI
   - Table: Username, Email, Role, Active
   - Actions: Add User, Edit, Deactivate, Reset Password

2. **Role Management** (`/admin/roles/`)
   - Define roles and their permissions
   - Django groups + permissions

**Business Logic:**

- **Decorator/Mixin:** Protect views with `@permission_required` or `LoginRequiredMixin` + `PermissionRequiredMixin`
- **Audit:** All models have `created_by`, `updated_by` (auto-set from request.user)

---

### Module 12: Document Management & File Uploads

**Purpose:** Store photos, PDFs, generated forms (Excel stores files in folders)

**Models:**

1. **`Document`**
   - `repair_job` (FK, optional - can also attach to bit, po, etc.)
   - `document_type` (Photo-Before, Photo-After, Photo-ADG, Evaluation-PDF, Quotation-PDF, Delivery-Ticket, Other)
   - `file` (FileField, upload to S3 or local storage)
   - `filename`
   - `description`
   - `uploaded_by`, `uploaded_at`

**Pages/Views:**

1. **Documents Tab** (in Repair Job Detail)
   - **List:** Document Type, Filename, Description, Uploaded By, Date
   - **Actions:** Upload, Download, Delete

2. **Upload Document** (`/repair-jobs/<work_order>/documents/upload/`)
   - **Form:** Document Type (dropdown), File (browse), Description
   - **Submit:** Save file, create Document record

3. **Auto-Generate Forms:**
   - **Evaluation Form PDF:** Button "Generate LSTK Evaluation PDF"
     - Render template with job data, evaluation grid
     - Use ReportLab or WeasyPrint to create PDF
     - Save as Document, download
   - **Quotation PDF:** Button "Generate Quotation PDF"
   - **Delivery Ticket PDF:** Button "Generate Delivery Ticket"

**Business Logic:**

- **File Storage:** Use Django `FileField` with S3 backend (django-storages) for scalability, or local `MEDIA_ROOT`
- **File Naming:** Auto-name files: `{work_order}_{document_type}_{timestamp}.{ext}`
- **Permissions:** Only users with `view_repairjob` permission can download documents

---

## Database Design Summary

### Core Tables

1. **Bit** (base serial units)
2. **BitRepairJob** (repair/evaluation instances)
3. **BitDesign** (MAT master)
4. **BOM** (bill of materials)
5. **CutterMap** (blade x pocket layout)
6. **EvaluationRecord** (cutter condition per job)
7. **CutterReplacementPlan** (ARDT vs Eng)
8. **Cutter** (cutter catalog)
9. **CutterOwnershipCategory** (lookup)
10. **CutterTransaction** (transaction log)
11. **CutterInventorySummary** (calculated/materialized view)
12. **CutterPriceHistory** (pricing over time)
13. **PurchaseOrder**, **PurchaseOrderLine**, **POShipment**
14. **ProcessStepDefinition**, **ProcessStep**
15. **QCChecklistDefinition**, **QCChecklistItem**
16. **Quotation**, **QuotationLine**
17. **LaborRateHistory**
18. **TechnicalInstruction**
19. **Customer**, **Supplier**
20. **Consumable**, **ConsumableTransaction**
21. **Document**
22. **User** (Django auth)

### Key Indexes

- `bit.base_serial_number` (unique, btree)
- `bit_repair_job.work_order_number` (unique, btree)
- `(bit_repair_job.bit_id, bit_repair_job.repair_revision)` (unique composite)
- `cutter.sap_number` (unique, btree)
- `cutter_transaction.cutter_id, cutter_transaction.date` (composite for fast queries)
- `evaluation_record.repair_job_id, evaluation_record.blade_number, evaluation_record.pocket_number` (composite unique)

### Foreign Keys

- All FKs use `ON DELETE PROTECT` by default (prevent accidental deletion)
- Exceptions: `Document.repair_job` uses `ON DELETE CASCADE` (delete documents when job deleted)

---

## Technology Stack

### Backend

- **Framework:** Django 5.2+ (latest stable)
- **Database:** PostgreSQL 16+ (with JSON support for flexible fields)
- **ORM:** Django ORM
- **API:** Django REST Framework (for AJAX endpoints, optional full REST API)
- **Background Tasks:** Celery + Redis (for inventory summary recalculation, email sending, report generation)
- **File Storage:** django-storages + AWS S3 (or local for dev)
- **PDF Generation:** WeasyPrint or ReportLab
- **Excel Import/Export:** openpyxl, pandas

### Frontend

- **Template Engine:** Django templates (Jinja2 optional)
- **CSS Framework:** Bootstrap 5.3+ (already in use per project analysis)
- **JavaScript:**
  - **Grid Editor:** Handsontable (free for non-commercial, or AG Grid)
  - **Charts:** Chart.js or Plotly
  - **Autocomplete:** Select2 or Django-Select2
  - **AJAX:** Axios or Fetch API
  - **Notifications:** Toastr or SweetAlert2
- **Icons:** Bootstrap Icons or Font Awesome

### DevOps

- **Version Control:** Git + GitHub
- **CI/CD:** GitHub Actions (run tests, deploy)
- **Deployment:** Docker + Gunicorn + Nginx (production)
- **Monitoring:** Sentry (error tracking), Django Debug Toolbar (dev)

---

## Migration Strategy

### Phase 1: Data Import

**Goal:** Load historical data from Excel without losing history

**Steps:**

1. **Create Django models** (all tables above)
2. **Run migrations** to create DB schema
3. **Write import scripts:**
   - `import_bits_tracking.py` - reads Bits Tracking workbook, creates Bit and BitRepairJob records
     - Parse SN to extract base_serial_number and repair_revision (e.g., "12721812R2" → SN=12721812, rev=2)
     - Create Bit if not exists
     - Create BitRepairJob per row
   - `import_cutter_transactions.py` - reads Cutter Consumption Updates sheet, creates CutterTransaction records
     - Preserve all transactions with original dates
     - Run summary calculation after import
   - `import_cutters.py` - reads Cutter Inventory sheet (row 2+), creates Cutter records
   - `import_consumables.py` - reads Consumables workbook, creates Consumable records
   - `import_boms.py` - reads BOM sheets (from job cards or separate BOM file), creates BOM and CutterMap records
4. **Validation:**
   - Count records in Excel vs DB (should match)
   - Spot-check data integrity (random sample of 20 bits, verify all fields correct)
   - Test queries (e.g., "all R2 repairs" - compare Excel filter vs DB query)
5. **Reconciliation:**
   - Run inventory summary calculation
   - Compare summary balances to Excel formulas (should match within rounding)

**Tools:**

- `openpyxl` to read Excel files
- Django management commands: `python manage.py import_bits_tracking`
- Progress bars: `tqdm` for long imports
- Error handling: Log rows that fail to import (e.g., invalid data), generate error report

### Phase 2: Parallel Run

**Goal:** New system runs alongside Excel for 1-2 months to validate

**Steps:**

1. **User Training:** Train evaluators, engineers, inventory clerks on new system
2. **Dual Entry:** Users enter new jobs in BOTH Excel (old way) and Django (new way)
3. **Daily Reconciliation:** At end of each day, compare:
   - Bits received (Excel vs DB)
   - Quotations generated (Excel vs DB)
   - Inventory transactions (Excel vs DB)
   - Flag discrepancies, investigate
4. **Feedback Loop:** Users report bugs, UI issues, missing features
5. **Iterate:** Fix bugs, improve UX

### Phase 3: Cutover

**Goal:** Switch to new system exclusively

**Steps:**

1. **Final Data Sync:** Import any Excel data entered during parallel run
2. **Lock Excel Files:** Mark old workbooks as read-only, archive
3. **Go Live:** All users switch to Django system
4. **Monitor:** First week, closely monitor for issues, provide support
5. **Retrospective:** After 1 month, gather user feedback, plan Phase 2 features

---

## Immediate Next Steps (Suggested Order)

1. **Set up Django project structure:**
   - Create apps: `bits`, `inventory`, `purchasing`, `reports`, `core`
   - Install dependencies: Django, psycopg2, celery, redis, openpyxl, etc.
   - Configure settings (database, static files, media, celery)

2. **Design and implement models:**
   - Start with core models: Bit, BitRepairJob, BitDesign, Cutter, CutterTransaction
   - Create migrations
   - Test model relationships in Django shell

3. **Implement Bit & Repair Job Management (Module 1):**
   - Views: Bit list, bit detail, repair job list, repair job detail
   - Forms: Create repair job
   - Templates: Use Bootstrap 5 for UI
   - Test with sample data

4. **Implement Cutter Evaluation Grid (Module 2):**
   - CutterMap, EvaluationRecord models
   - Handsontable integration for grid UI
   - AJAX save for real-time updates
   - Test with sample bit design

5. **Implement Cutter Inventory (Module 4):**
   - CutterTransaction model
   - Inventory dashboard, detail views
   - Transaction log entry
   - Summary calculation (start with real-time query, optimize later)
   - Test with sample transactions

6. **Implement BOM & Cutter Map Editor (Module 3):**
   - BOM editor UI
   - Cutter map visual editor
   - Test creating new bit design

7. **Implement Quotation (Module 5):**
   - Quotation, QuotationLine models
   - Auto-generate quotation from cutter plan
   - Quotation editor
   - PDF export
   - Test with sample repair job

8. **Implement Purchase Orders (Module 6):**
   - PO models
   - PO CRUD views
   - GRN posting → inventory transaction
   - Test with sample PO

9. **Implement Process Routing & QC (Module 7):**
   - ProcessStep, QCChecklist models
   - Router sheet view
   - Checklist forms
   - Test with sample job

10. **Implement Reports (Module 10):**
    - Dashboard KPIs
    - Bits report, cutter consumption report
    - Export to Excel
    - Test with imported historical data

11. **Implement Technical Instructions (Module 8):**
    - TechnicalInstruction model
    - Instruction CRUD
    - Relevant instructions widget
    - Test with sample instructions

12. **Implement Consumables (Module 9):**
    - Consumable model
    - Consumable catalog, transactions
    - Test with sample consumables

13. **Implement Document Management (Module 12):**
    - Document model
    - File upload views
    - Auto-generate evaluation/quotation PDFs
    - Test with sample uploads

14. **Implement User Management (Module 11):**
    - Define roles and permissions
    - Protect views
    - Test with different user roles

15. **Write Data Import Scripts:**
    - import_bits_tracking
    - import_cutter_transactions
    - import_cutters
    - import_boms
    - Run on real Excel data
    - Validate results

16. **User Training & Parallel Run:**
    - Create user documentation
    - Train users
    - Begin parallel run
    - Daily reconciliation

17. **Cutover:**
    - Final data sync
    - Lock Excel
    - Go live

---

## Key Considerations

### Performance

- **Inventory Summary Calculation:** With millions of transactions, real-time calculation will be slow. Use materialized view or Celery task to pre-calculate and refresh hourly.
- **Large Evaluation Grids:** 12 blades × 34 pockets = 408 cells. Use AJAX to save individual cells (not entire form submit). Pagination if needed.
- **Reporting:** Large date ranges with many jobs. Use DB indexing (on dates, statuses), pagination, and optional caching.

### Data Integrity

- **Constraints:** Use DB constraints (unique, foreign key, check) to prevent bad data.
- **Validation:** Django model validators and form validators.
- **Audit Trail:** All changes logged (created_by, updated_by, timestamps).
- **Soft Delete:** Use `is_deleted` flag instead of hard delete for critical records (can recover if mistake).

### User Experience

- **Speed:** Optimize queries (select_related, prefetch_related), cache where appropriate.
- **Search:** Implement autocomplete for serial numbers, MAT numbers, cutter SAP numbers.
- **Mobile-Friendly:** Responsive design (Bootstrap responsive classes). Operators on shop floor may use tablets.
- **Notifications:** Email or in-app notifications for key events (job assigned, quotation approved, cutter shortage).

### Security

- **Authentication:** Require login for all pages (except maybe public reports if needed).
- **Authorization:** Role-based permissions (see Module 11).
- **HTTPS:** Use HTTPS in production (prevent interception of data).
- **CSRF Protection:** Django's built-in CSRF protection enabled.
- **SQL Injection:** Use Django ORM (parameterized queries) - don't write raw SQL unless necessary.
- **File Upload Validation:** Validate file types, sizes (prevent malicious uploads).

### Scalability

- **Database:** PostgreSQL can handle millions of rows. Use indexes, optimize queries.
- **File Storage:** Use S3 or similar for file storage (don't store large files in DB).
- **Background Tasks:** Offload heavy tasks (email sending, report generation, inventory calculation) to Celery.
- **Caching:** Use Redis or Memcached for caching expensive queries (e.g., dashboard KPIs).

### Extensibility

- **Modular Design:** Each module (bits, inventory, purchasing) is a Django app. Can add new apps later (e.g., `shipping`, `quality`).
- **API:** If future integration needed (mobile app, external systems), expose Django REST Framework API.
- **Customization:** Use Django's built-in admin for quick CRUD, but build custom UIs for complex workflows (evaluation grid, quotation editor).

---

## Testing Strategy

1. **Unit Tests:**
   - Test model methods (e.g., `bit.get_latest_repair()`, `quotation.calculate_total()`)
   - Test form validation
   - Run: `python manage.py test`

2. **Integration Tests:**
   - Test views (create repair job, enter evaluation, generate quotation)
   - Test transactions (PO receipt → inventory update)
   - Use Django test client

3. **Manual Testing:**
   - User acceptance testing (UAT) during parallel run
   - Test with real users, real data

4. **Performance Testing:**
   - Load test inventory summary calculation with 1M transactions
   - Load test evaluation grid with 408 cells
   - Use `django-debug-toolbar` to profile queries

5. **Regression Testing:**
   - After each new feature, re-test existing features to ensure no breakage
   - Automated tests help catch regressions

---

## Documentation Requirements

1. **Technical Documentation:**
   - ER diagram (database schema)
   - API documentation (if REST API exposed)
   - Deployment guide
   - Backup/restore procedures

2. **User Documentation:**
   - User manual (PDF or online help)
   - Video tutorials (screen recordings)
   - Quick start guide
   - FAQs

3. **Code Documentation:**
   - Docstrings for all models, views, functions
   - Comments for complex business logic
   - README.md in each app directory

---

## Success Criteria

**The implementation is successful if:**

1. ✅ **Data Migrated:** All historical data from Excel is in the DB with 100% accuracy (no data loss).
2. ✅ **Feature Parity:** All Excel workflows (job card, tracking, inventory, PO, quotation) work in Django.
3. ✅ **User Adoption:** Users can perform all tasks without needing Excel (may refer to Excel for historical lookup initially, but all new work in Django).
4. ✅ **Performance:** Pages load in < 2 seconds, reports generate in < 10 seconds (for typical date ranges).
5. ✅ **Reliability:** System is stable, no critical bugs, uptime > 99%.
6. ✅ **Audit Trail:** All changes are logged, can trace "who changed what when".
7. ✅ **Concurrent Access:** Multiple users can work simultaneously without conflicts or file locking.
8. ✅ **Reports:** Users can generate all reports they need (bits, cutter consumption, financial, operator performance).
9. ✅ **Alerts:** Inventory shortage alerts work, email notifications work.
10. ✅ **User Satisfaction:** Users prefer the new system over Excel (survey or feedback).

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Data loss during migration** | High | Low | Backup Excel files, test import scripts on copy, validate counts |
| **Users reject new system** | High | Medium | Involve users early, train well, parallel run, gather feedback |
| **Performance issues (slow queries)** | Medium | Medium | Optimize queries, use indexing, caching, materialized views |
| **Scope creep (too many features)** | Medium | High | Prioritize core features (MVP), defer nice-to-haves to Phase 2 |
| **Underestimating complexity** | Medium | Medium | Break into small modules, test each module, use agile approach |
| **Integration with ERP fails** | Medium | Low | Start with manual export/import, plan API integration for Phase 2 |
| **Bugs in production** | Medium | Medium | Thorough testing, staged rollout, monitoring, quick rollback plan |

---

## Conclusion

This implementation prompt provides a comprehensive blueprint for rebuilding the Excel-based PDC Bit Manufacturing & Repair Management System in Django + PostgreSQL. By following this spec, you will:

- **Eliminate Excel's limitations:** Concurrent access, no file locking, no formula fragility
- **Improve data integrity:** Database constraints, validation, referential integrity
- **Enhance user experience:** Modern web UI, search/filter, autocomplete, dashboards
- **Enable scalability:** Handle millions of rows, support business growth
- **Provide auditability:** Track all changes, comply with quality standards
- **Facilitate reporting:** Generate custom reports, export to Excel/PDF
- **Support workflows:** Process routing, approvals, notifications
- **Integrate with ERP:** API-ready for future integration

**Start with Module 1 (Bit & Repair Job Management)**, get it working end-to-end, then build out the other modules incrementally. Use the migration strategy to import historical data and run parallel for validation before cutover.

Good luck!

---


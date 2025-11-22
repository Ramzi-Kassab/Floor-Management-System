### 2. Bits Tracking: `Copy of BITS TRACKING 7-6-2025.xlsx`

#### Overview

**File:** `Copy of BITS TRACKING 7-6-2025.xlsx`
**Sheets:** 26
**Purpose:** Master registry of ALL bits ever received for repair/evaluation across all customers and locations

**Sheet List:**
1. `LSTK` - LSTK bits tracking (primary customer)
2. `Sheet1` - Scratch/unused
3. `UR` - UR (customer/location specific)
4. `L3` - Level 3 bits tracking
5. `L4` - Level 4 bits tracking
6. `ARDT` - ARDT facility bits
7. `WFD` - White Finger Design bits
8. `CheckGaps` - Gap analysis/validation
9. `Sheet4` - Scratch/unused
10. `ARAMCO` - Saudi ARAMCO bits
11. `Batch 3 required cutters` - Cutter requirements for batch
12. `RC-LSTK` - Reclaimed LSTK bits
13. `HALLIBURTON` - Halliburton bits
14. `Hal_Regional` - Halliburton regional
15. `General bits Tracking` - General tracking view
16. `REAMERS` - Reamer tools tracking
17. `Collect Data` - Data collection sheet
18. `ARAMCO REPAIR UPDATE` - ARAMCO repair status updates
19. `DATA` - Data entry/lookup
20. `CF2 & SENSORS` - CF2 and sensor bits
21. `ARDTAR` - ARDT AR (ARAMCO?) bits
22. `LITHIUM BATTERY LOG` - Lithium battery tracking
23. `SUB` - Sub-assembly tracking
24. `ARDT-CR` - ARDT customer returns
25. `ARDTS` - ARDT specialized bits
26. `Buffer` - Buffer/scratch sheet

**Total Rows:** Over 1 million rows across all sheets (LSTK sheet alone: 1,046,734 rows!)

---

#### Sheet: `LSTK` (LSTK Customer Bits Tracking)

**Dimensions:** 1,046,734 rows × 36 columns

**Purpose:**
Master register of all bits received from LSTK customer. Tracks entire lifecycle from receipt through repair/scrap to delivery.

**Column Headers:**

| Column | Header | Purpose |
|--------|--------|---------|
| A | `ORDER NO.` | Work order number (e.g., 20161255) |
| B | `SERIAL NO` | Bit serial number (e.g., 11890943, 12721812R2) |
| C | `SIZE` | Bit size (e.g., 6 1/8", 12 1/4") |
| D | `TYPE` | Bit type (e.g., FMD44, MMD63, MMG64H) |
| E | `MAT NO.` | Material/design number (e.g., 702617, 952071) |
| F | `RECIVED` | Date received (e.g., 2017-01-02) |
| G | `FROM` | Source/customer |
| H | `Origional MAT Level` | Original MAT level (L3/L4/L5) |
| I | `NEW TYPE` | New type if redesigned |
| J | `STATUS` | Current status (e.g., HOLD, Repair, Scrap) |
| K | `FINAL` | Final disposition |
| L | `Upper Section Replacement` | Yes/No for upper section work |
| M | `Build up` | Build-up operation |
| N | `Brazer` | Brazing technician |
| O | `Spinner` | Spinning technician |
| P | `Tip Grinding by` | Tip grinding operator |
| Q | `QC` | QC inspector |
| R | `Thread Cleaning / Machining` | Thread work operator |
| S | `Body Cleaning / Machining` | Body work operator |
| T | `Erosion sleeve` | Erosion sleeve work |
| U | `Rework` | Rework indicator |
| V | `ACCOMPLISHED DATE` | Completion date |
| W | `REMARKS` | Free-text remarks |
| X | `Job Name` | Job/project name |
| Y | `Issues report` | Issues encountered |
| Z | `PDC Production Days` | Days in production |
| AA | `Lost Cutter` | Lost cutter tracking |
| AB | `ITEM NUMBER` | ERP item number |
| AC | `MJ #` | MJ reference number |
| AD | `Production Order Number` | ERP production order |
| ... | ... | (additional columns) |

**Sample Data:**

| ORDER NO. | SERIAL NO | SIZE | TYPE | MAT NO. | RECIVED | STATUS |
|-----------|-----------|------|------|---------|---------|--------|
| 20161255 | 11890943 | 6 1/8" | FMD44 | 702617 | | HOLD |
| 20171007 | 12721812R2 | 6 1/8" | MMD63 | 952071 | 2017-01-02 | Repair |
| 20171057 | 12652742R | 6 1/8" | MMG64H | 953042 | 2017-01-22 | HOLD |
| 20171089 | 12679502R | 6 1/8" | MMG64H | 953042 | | HOLD |
| 20171162 | 12693583R1 | 6 1/8" | MME63 | 965530 | 2017-03-13 | HOLD |

**Key Observations:**

1. **Serial Number Format:** `12721812R2` = Base SN `12721812` + Repair Revision `R2`
   - First repair: `R` or `R1`
   - Second repair: `R2`
   - Third repair: `R3`, etc.
   - **LEGACY ISSUE:** SN and revision are concatenated in ONE field

2. **Status Values:** HOLD, Repair, Scrap, Delivered, In Progress, etc.

3. **Historical Data:** Data goes back to 2016-2017, preserving full history

4. **Sparse Data:** Many rows have only partial data (some columns empty)

5. **Formulas Present:**
   ```excel
   // Row 7, Col T
   =IFERROR(SMALL($AF$2:$AF$549,ROWS(L$2:$AF7)),"")

   // Row 2, Col AF
   =IFERROR(IF($AA$1<>0,IF($AA$1=VALUE(#REF!),AG2,""),""),"")
   ```

**Business Logic:**

1. Bit received → entered in tracking sheet with SN, Size, Type, MAT, Date
2. As bit moves through workflow → operators update their columns (Brazer, Spinner, QC, etc.)
3. Final status updated (Repair complete, Scrap, Returned)
4. Accomplished date recorded
5. If bit returns for 2nd repair → new row with `SN + R1` or `R2`

**Usage:**

- Quick lookup of bit history by serial number
- Status reporting (how many bits in each stage)
- Operator workload tracking
- Days-in-production analysis
- ERP integration via ITEM NUMBER and Production Order Number

---

#### Other Customer Sheets (ARAMCO, HALLIBURTON, etc.)

**Structure:** Similar to LSTK sheet with customer-specific customizations

**Key Differences:**
- ARAMCO may have contract-specific fields
- Halliburton may have different MAT number formats
- Regional sheets may have location-specific tracking

---

#### Sheet: `L3` and `L4` (Level-Based Tracking)

**Purpose:** Track bits by MAT level (L3 vs L4) for different product lines or manufacturing processes.

---

#### Key Insights from Bits Tracking Workbook

**Strengths:**
- Comprehensive historical record
- Customer segmentation
- Operator accountability
- ERP integration fields present

**Weaknesses/Legacy Issues:**
- **SN + Revision in ONE field** (`12721812R2`) → should be separate `serial_number` and `repair_revision` in DB
- **No audit trail** - can't see who updated what field when
- **Difficult to query** - "Show me all R2 repairs" requires text parsing
- **Duplicate data** - same bit info in both tracking and job card workbooks
- **Manual synchronization** - job card completion doesn't auto-update tracking sheet
- **Status inconsistency** - freeform text allows typos ("Repair" vs "Repairs" vs "In Repair")
- **No validation** - can enter SN that doesn't exist
- **Performance issues** - 1 million rows makes Excel slow

**Data to Preserve:**
- Serial number (split into base SN + revision)
- All historical records (don't lose history when migrating)
- Status timeline (when did it enter each stage)
- Operator assignments
- Remarks and issues
- ERP reference numbers

---

### 3. Cutter Inventory: `Copy of Cutter Inventory 11-18-2025.xlsx`

#### Overview

**File:** `Copy of Cutter Inventory 11-18-2025.xlsx`
**Sheets:** 20
**Purpose:** Cutter availability forecasting, consumption tracking, and procurement planning

**Sheet List:**
1. `Cutters Inventory 11-9-2025` - Main inventory summary
2. `Sheet3, Sheet5, Sheet1, Sheet2` - Scratch/calculation helpers
3. `ARAMCO 3D BATCH 7.7.2022` - ARAMCO batch tracking
4. `Special Consumables_C&S_.. (2)` - Special consumables
5. `Categories Data` - Cutter categorization
6. `L3&L4 BOMs & Cutters 11-9-2025` - BOM-to-cutter mapping
7. `Obsolete Cutters-10-27-2025` - Obsolete cutter list
8. `Cutters Orders Updates` - Purchase order tracking
9. `Cutters Consumption Updates` - Transaction log (additions/subtractions)
10. `BOMS` - Bill of materials
11. `FILTER` - Filter/lookup helper
12. `Check` - Validation checks
13. `Special Consumables_C&S_CF2.0` - CF2.0 consumables
14. `Azim's update 9.27.2023, 9.1.2022` - Historical updates
15. `ENO Cracked Cutters` - Cracked cutter tracking
16. `BITS WITH MODIFIED CUTTERS` - Modified cutter bits

---

#### Sheet: `Cutters Inventory 11-9-2025` (Main Summary)

**Dimensions:** 304 rows × 46 columns

**Purpose:**
Real-time cutter availability summary with forecasting, safety stock calculations, and shortage alerts.

**Column Headers:**

| Column | Header | Purpose |
|--------|--------|---------|
| A | `#` | Row number |
| B | `SAPNo` | SAP/ERP material number (e.g., 802065, 179692) |
| C | `Type` | Cutter type (Round, IA-STL, Shyfter, Short Bullet) |
| D | `Cutter size` | Size (e.g., 1313, 1308, 13MM Long, 1613, 19MM) |
| E | `Type` | Cutter grade (CT97, ELITE RC, M1, CT62, CT36) |
| F | `Chamfer` | Chamfer size (e.g., 0.010", 0.018", 0.012R) |
| G | `More Description` | Additional description |
| H | `Category` | Categorization (P-Premium, O-Other, D-Depth of Cut, B-Standard, S-Super Premium) |
| I | `ENO As New Cutter` | **Formula:** ENO (External New Original) cutters treated as new |
| J | `ENO Ground Cutter` | **Formula:** ENO cutters after grinding |
| K | `ARDT Reclaim Cutter` | **Formula:** Cutters reclaimed by ARDT |
| L | `LSTK Reclaim Cutter` | **Formula:** Cutters reclaimed from LSTK bits |
| M | `New Stock` | **Formula:** Brand new cutters in stock |
| N | `Total New` | **Formula:** `= M + I` (New + ENO As New) |
| O | `6 months consumption` | **Formula:** SUMIFS consumption in last 182 days |
| P | `3 months consumption` | **Formula:** SUMIFS consumption in last 91 days |
| Q | `2 months consumption` | **Formula:** Calculated from 3-month |
| R | `Safety Stock` | **Formula:** Complex tiered calculation |
| S | `Category` | Classification |
| T | `BOM requirement (11/9/2025)` | **Formula:** Total cutters needed for bits currently in production |
| U | `On Order (11/9/2025)` | **Manual:** Cutters on order from suppliers |
| V | `Total Stock - Forcast` | **Formula:** Current stock - BOM requirement + On Order |
| W | `Remarks` | Free-text remarks (e.g., "SHORTAGE", "OK", "EXCESS") |
| X | `Replacement` | Replacement cutter part number |
| Z | `L3 & 4` | L3/L4 BOM requirement |
| ... | ... | ... |

**Sample Data:**

| # | SAPNo | Type | Size | Grade | Chamfer | Category | ENO As New | ENO Ground | New Stock | Total New | 6mo Consumption | Safety Stock |
|---|-------|------|------|-------|---------|----------|------------|------------|-----------|-----------|-----------------|--------------|
| 1 | 802065 | Round | 1313 | CT97 | 0.010" | P-Premium | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA |
| 2 | 179692 | Round | 1313 | ELITE RC | 0.018" | O-Other | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA |
| 3 | 179694 | Round | 1308 | ELITE RC | 0.018" | O-Other | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA | =FORMULA |

**Key Formulas:**

**1. ENO As New Cutter (Column I, Row 2):**

```excel
=SUMIFS('Cutters Consumption Updates'!$F:$F,
        'Cutters Consumption Updates'!$D:$D, I$1,
        'Cutters Consumption Updates'!$B:$B, $B2)
 - SUMIFS('Cutters Consumption Updates'!$E:$E,
          'Cutters Consumption Updates'!$D:$D, I$1,
          'Cutters Consumption Updates'!$B:$B, $B2)
 + SUMIF('Cutters Consumption Updates'!$AS:$AS, $B2,
         'Cutters Consumption Updates'!AT:AT)
```

**Translation:**
- Sum all additions (Column F) for this cutter SAP# where ownership type = "ENO As New"
- Subtract all subtractions (Column E)
- Add any manual adjustments

**2. 6 Months Consumption (Column O, Row 2):**

```excel
=SUMIFS('Cutters Consumption Updates'!E:E,
        'Cutters Consumption Updates'!B:B, B2,
        'Cutters Consumption Updates'!A:A, ">" & TODAY()-182)
```

**Translation:**
- Sum consumption (Column E) for this cutter where date > (today - 182 days)

**3. 2 Months Consumption (Column Q, Row 2):**

```excel
=IF(O2<>0, _xlfn.CEILING.MATH(O2/3), 0)
```

**Translation:**
- Divide 6-month consumption by 3, round up (assumes even consumption rate)

**4. Safety Stock (Column R, Row 2):**

```excel
=IF(Q2<=1, 0,
   CEILING(
      IF(Q2>=300, Q2+10,
      IF(Q2>=200, Q2+5,
      IF(Q2>=100, Q2+5,
      IF(Q2>=50, Q2+2,
      IF(Q2>=20, Q2+2,
      IF(Q2>=10, Q2+2,
      IF(Q2>=5, Q2+2,
      Q2+1))))))), 5))
```

**Translation:**
- Tiered safety stock buffer:
  - Consumption ≥ 300: add 10
  - Consumption ≥ 200: add 5
  - Consumption ≥ 100: add 5
  - Consumption ≥ 50: add 2
  - Consumption ≥ 20: add 2
  - Consumption ≥ 10: add 2
  - Consumption ≥ 5: add 2
  - Consumption < 5: add 1
- Round up to nearest 5

**5. Total Stock - Forecast (Column V):**

```excel
= (Total New + ENO Ground + ARDT Reclaim + LSTK Reclaim)
  - BOM requirement
  + On Order
```

---

#### Sheet: `Cutters Consumption Updates` (Transaction Log)

**Purpose:**
**Transaction-level log** of every cutter addition and subtraction. This is the source data for all formulas in the main inventory sheet.

**Columns:**
- `A`: Date
- `B`: SAPNo (cutter part number)
- `C`: Description
- `D`: Ownership Type (ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock, Retrofit)
- `E`: Subtraction (quantity consumed/used)
- `F`: Addition (quantity received/reclaimed)
- Additional columns for adjustments and corrections

**Sample Transaction:**

| Date | SAPNo | Description | Ownership Type | Subtraction | Addition |
|------|-------|-------------|----------------|-------------|----------|
| 2025-01-15 | 802065 | Bit 14204328 | New Stock | 8 | 0 |
| 2025-01-10 | 802065 | PO-2025-003 | New Stock | 0 | 100 |
| 2024-12-20 | 802065 | Reclaimed from 13824396 | ENO As New | 0 | 6 |

**Business Logic:**

1. **Addition transactions:**
   - Receive new stock from supplier → Addition in "New Stock"
   - Reclaim cutters from used bit → Addition in "ENO As New" or "ARDT Reclaim"
   - Grind ENO cutters → Subtract from "ENO As New", Add to "ENO Ground"

2. **Subtraction transactions:**
   - Consume cutters for repair job → Subtraction from appropriate category
   - Scrap damaged cutters → Subtraction

3. **Formula aggregation:**
   - Main inventory sheet sums all transactions per cutter per category
   - Real-time balance calculation

---

#### Sheet: `L3&L4 BOMs & Cutters 11-9-2025` (BOM Requirements)

**Purpose:**
Links bits currently in production (from bits tracking) to their BOMs, calculates total cutter requirements.

**Columns:**
- Bit serial number
- MAT number
- BOM line items (each cutter type needed)
- Quantities per bit
- Total quantities needed across all bits

**Formula Logic:**

For each cutter part number, count how many times it appears in active BOMs and sum quantities.

**Feed to Main Inventory:**

The `BOM requirement` column (T) in main inventory sheet pulls from this sheet.

---

#### Sheet: `Cutters Orders Updates` (PO Tracking)

**Purpose:**
Track purchase orders for cutters from suppliers.

**Columns:**
- PO Number
- Date
- SAPNo (cutter part number)
- Quantity ordered
- Quantity received
- Balance
- Expected delivery date
- Status

**Feed to Main Inventory:**

The `On Order` column (U) in main inventory pulls from this sheet (sum of open POs).

---

#### Key Insights from Cutter Inventory Workbook

**Strengths:**
- **Sophisticated forecasting** with consumption trends
- **Multiple ownership categories** (ENO, ARDT, LSTK, New)
- **Tiered safety stock logic**
- **Transaction-level detail** preserved
- **BOM integration** for demand forecasting

**Weaknesses/Legacy Issues:**
- **Formula-heavy** - all calculations in Excel, slows down with data growth
- **No concurrent editing** - only one user can update consumption log
- **Manual on-order entry** - must manually update Column U from PO system
- **No alerts** - must manually scan for shortage remarks
- **Data entry errors** - typos in SAPNo cause formula failures
- **Category inconsistency** - "ENO As New" vs "ENO-As-New" breaks formulas
- **No workflow** - transactions entered ad-hoc, no approval process
- **Difficult to audit** - can't easily trace "who added this transaction when"

**Data Model for DB:**

**Tables needed:**
1. **`CutterMaster`**: Cutter catalog (SAPNo, Type, Size, Grade, Chamfer, Category)
2. **`CutterOwnershipCategory`**: Lookup (ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock)
3. **`CutterTransaction`**: Transaction log (date, cutter_id, ownership_category_id, addition_qty, subtraction_qty, reference_type, reference_id, created_by, created_at)
4. **`CutterInventorySummary`**: **Materialized view** or calculated report (cutter_id, ownership_category_id, current_balance, 6mo_consumption, safety_stock, bom_requirement, on_order, forecast)
5. **`CutterPurchaseOrder`**: PO tracking (po_number, cutter_id, qty_ordered, qty_received, expected_date, status)

**Business Logic in DB:**

- **Trigger or scheduled job** to recalculate inventory summary from transaction log
- **Automated alerts** when forecast < safety stock
- **Validation** to prevent invalid SAPNo entry
- **Audit trail** automatic (created_by, created_at, updated_by, updated_at)
- **Concurrent transactions** with proper locking

---

### 4. ERP Reconciliation: `Cutter inventory by inventory dimension-Oct-2025.xlsx`

#### Overview

**File:** `Cutter inventory by inventory dimension-Oct-2025.xlsx`
**Sheets:** 6
**Purpose:** Reconcile physical cutter inventory with Microsoft Dynamics ERP system

**Key Sheet: `Summary`**

**Purpose:**
Side-by-side comparison of ERP quantities vs physical count for each cutter.

**Columns:**

| Column | Header | Source |
|--------|--------|--------|
| A | MAT | Cutter MAT number |
| B-F | ERP columns | ENO, NEW, RCLM, RCLM-ARDT, Total from ERP |
| G-K | Physical columns | ENO, NEW, RCLM, RCLM-ARDT, Total from physical count |
| M | Variance | `=Physical Total - ERP Total` |

**Sample:**

| MAT | ERP ENO | ERP NEW | ERP Total | Physical ENO | Physical NEW | Physical Total | Variance |
|-----|---------|---------|-----------|--------------|--------------|----------------|----------|
| 177778 | 0 | 3 | 3 | 0 | 3 | 3 | 0 |
| 179692 | 12 | 0 | 12 | 12 | 0 | 12 | 0 |
| 179733 | 0 | 173 | 197 | 0 | 173 | 197 | 0 |

**Purpose:**
- Identify discrepancies between ERP and physical inventory
- Prepare for ERP migration
- Ensure data quality before go-live

---

### 5. Purchase Orders: `new version of PO Customs- updated.xlsx`

#### Overview

**File:** `new version of PO Customs- updated.xlsx`
**Sheets:** 2
**Purpose:** Track purchase orders through receiving, customs clearance, and GRN (Goods Receipt Note)

**Key Sheet: `Small Parts`**

**Dimensions:** 2,468 rows × 23 columns

**Columns:**

| Column | Header | Purpose |
|--------|--------|---------|
| A | `PO` | Purchase order number (e.g., 2022-003) |
| B | `Date` | PO date |
| C | `Item` | Item number on PO |
| D | `Ordered Qty` | Quantity ordered |
| E | `Rec in our facility` | **Formula:** Received in facility |
| F | `Remaining in Production` | **Formula:** Remaining with supplier |
| G | `STATUS` | CLOSED, OPEN, IN TRANSIT, etc. |
| H | `Description` | Item description (e.g., "1608 .018,18C, CT200") |
| I | `MN` | Material Number (ERP reference) |
| J | `Required Date` | **Formula:** `=B2+30` (PO date + 30 days) |
| K | `S/O` | Sales order reference |
| L | `Rec in ARDT` | Received at ARDT facility |
| M | `In Trans` | In transit |
| N | `Ready to ship` | Ready to ship from supplier |
| O | `In Halliburton production` | At Halliburton production facility |
| P | `AWB No#` | Air Waybill number |
| Q | `Shipping Date` | Shipped date |
| R | `ETA Date` | Estimated arrival |
| S | `Clearance ETA` | Customs clearance ETA |
| T | `Recd Date` | Actual received date |
| U | `GRN NO` | Goods Receipt Note number |
| V | `ERP GRN` | ERP system GRN number |
| W | `PML Update` | PML (person) update |

**Formula Examples:**

```excel
// Column E: Received in our facility
=IF(D2<>"", SUMIFS($A$2:$W$4257, $L$2:$L$4257, $A$2:$A$4257, A2, $C$2:$C$4257, C2), "")

// Column J: Required Date
=B2+30  // PO date + 30 days
```

**Business Logic:**

1. Create PO → enter PO#, Date, Items, Ordered Qty
2. Track shipment → update AWB, Shipping Date, ETA
3. Customs clearance → update Clearance ETA
4. Receive → update Rec Date, GRN NO
5. Post to ERP → update ERP GRN
6. Status auto-calculated based on quantities and dates

---

### 6. Consumables Catalog: `Consumables and Spare Parts-PDC 11-4-2025.xlsx`

#### Overview

**File:** `Consumables and Spare Parts-PDC 11-4-2025.xlsx`
**Sheets:** 6
**Purpose:** ERP-ready catalog of consumables and spare parts for Microsoft Dynamics

**Key Sheet: `Master Data 11-4-2025`**

**Dimensions:** 286 rows × 16,382 columns (!!!)

**Note:** Extremely wide sheet due to product dimension combinations (configurations, sizes, colors, styles).

**Columns (first 20):**

| Column | Header | Purpose |
|--------|--------|---------|
| A | `Item Number` | Auto-assigned by ERP (e.g., FS-0678, CN-000208) |
| B | `Product Name` | ERP-recognized item name |
| C | `Search Name` | Layman's terms or common name |
| D | `Product Type` | Item / Service |
| E | `Product Subtype` | Product / Product Master |
| F | `Item Group` | Grouping category |
| G | `Inventory Unit` | EA, Kilogram, etc. |
| H | `Item Model Group` | Inventory behavior (PhyInv by default) |
| I | `Storage dimension group` | Warehouse/location control (SWL by default) |
| J | `Tracking dimension group` | None by default |
| K | `Configurations` | Product configurations |
| L | `Sizes` | Size variations |
| M | `Colors` | Color variations |
| N | `Styles` | Style variations |
| O | `Equipment` | Related equipment |
| P | `Quarterly Consumption` | Estimated quarterly usage |
| Q | `Minimum Buffer Stock Required 6 months` | Formula: `=8*365` (example) |
| R | `Image (Link or File Ref)` | Image reference |
| S | `Expanded Configurations` | Full configuration matrix |
| T | `Source` | Supplier source |
| U | `Links` | Web links or references |

**Sample Data:**

| Item Number | Product Name | Search Name | Type | Subtype | Unit | Model Group |
|-------------|--------------|-------------|------|---------|------|-------------|
| FS-0678 | Sand Blasting gloves- Right | SandBlastingGlovesRi | Item | Product Master | EA | Phyinv |
| FS-0679 | Sand Blasting gloves- Left | SandBlastingGlovesLe | Item | Product Master | EA | Phyinv |
| FS-0473 | Cast Acrylic Sheet | CastAcrylicSheet | Item | Product Master | EA | Phyinv |
| FS-0279 | Blasting Media (Aluminum Oxide 100 grit) | BlastingMediaAluminu | Item | Product Master | Kilogram | Phyinv |
| CN-000208 | Flux Handy B-1 paste Black 1 LB | FluxHandyB1PasteBlac | Item | Product Master | EA | Phyinv |

**Purpose:**
- Prepare consumables data for ERP import
- Standardize item numbers and names
- Define product dimensions and attributes
- Establish inventory policies

---

## Key Business Processes Identified

### Process 1: Bit Repair Job Card Workflow

**Steps:**

1. **Bit Receipt**
   - Customer returns bit for repair/evaluation
   - Receive SN, Size, Type, MAT, Customer
   - Enter in Bits Tracking sheet (new row or R1/R2 revision)

2. **Create Job Card**
   - Copy job card template
   - Rename file: `YYYY-SOURCE-MAT-REVISION-SN.xlsx` (e.g., `2025-ARDT-LV4-015-14204328.xlsx`)
   - Enter bit data in `Data` sheet rows 1-10

3. **Process Routing**
   - Bit flows through workflow steps (Nozzle Removal, Washing, Sand Blasting, Die Check, etc.)
   - Operators sign and date in `Router Sheet`

4. **Evaluation**
   - Evaluator inspects bit physically
   - Marks cutters in `Data` sheet grid (columns BR onwards) with symbols: X, O, R, S, L, V, P, I, B
   - Evaluation formulas populate `Evaluation`, `Eval-LSTK`, `Eval & Quot-AR` sheets

5. **Cutter Entry**
   - ARDT technician marks cutters to replace in `ARDT Cutter Entry` (X marks)
   - Summary calculates quantities needed per cutter part number

6. **Engineering Review**
   - Engineer reviews and may override in `Eng. Cutter Entry`
   - Engineering approval drives final quantities

7. **Quotation**
   - `Quotation` sheet auto-calculates costs:
     - Cutter quantities × unit prices
     - Labor (process steps × rates)
     - Materials (consumables)
     - Overhead and margin
   - Print quotation for customer approval

8. **Repair Execution**
   - If approved, execute repair per `Instructions` sheet
   - Operators complete steps and sign `Router Sheet`
   - QC checks via `E checklist`, `API Thread Inspection`, `Die Check Entry`

9. **Final Inspection**
   - QC approves
   - Print customer-specific evaluation form (LSTK, ARAMCO, etc.)
   - Print Delivery Ticket

10. **Update Tracking**
    - Manually update Bits Tracking sheet with completion date, status, operators

11. **Delivery**
    - Package with paperwork
    - Deliver to customer
    - Update status to "Delivered"

**Data Created:**
- Job card file (saved in folder named `YYYY-SOURCE-MAT-REVISION-SN`)
- Photos (before, after, ADG - Auto Dull Grade)
- PDF exports of evaluation forms, quotation, delivery ticket

---

### Process 2: Cutter Inventory Management

**Steps:**

1. **Receive New Cutters (PO)**
   - Supplier ships cutters
   - Track in `PO Customs` sheet through customs, GRN
   - Once received, add transaction in `Cutters Consumption Updates`:
     - Date, SAPNo, Description, "New Stock", Addition = qty

2. **Reclaim Cutters from Bit**
   - After de-brazing bit, recover reusable cutters
   - Inspect cutters
   - Classify:
     - ENO As New (excellent condition, original cutter)
     - ENO Ground (needs grinding)
     - ARDT Reclaim (ARDT facility reclaim)
     - LSTK Reclaim (from LSTK customer bits)
   - Add transaction in `Cutters Consumption Updates`:
     - Date, SAPNo, Description, Ownership Type, Addition = qty

3. **Grind ENO Cutters**
   - Take ENO As New cutters, grind to restore geometry
   - Subtract from "ENO As New"
   - Add to "ENO Ground"
   - Two transactions in `Cutters Consumption Updates`

4. **Consume Cutters for Repair**
   - Repair job consumes cutters per job card
   - Subtract transaction in `Cutters Consumption Updates`:
     - Date, SAPNo, Description (Job SN), Ownership Type, Subtraction = qty
   - Deduct from highest-priority category (typically New Stock first, then ENO As New, then reclaimed)

5. **Forecast & Procurement**
   - Weekly review `Cutters Inventory` sheet
   - Identify shortages (forecast < safety stock)
   - Create purchase requisition
   - Track in `Cutters Orders Updates`
   - Update `On Order` column manually

6. **BOM Requirements**
   - Bits in production drive cutter demand
   - `L3&L4 BOMs & Cutters` sheet calculates total BOM requirements
   - Feed to `BOM requirement` column in main inventory

7. **Reconciliation**
   - Periodic physical count
   - Compare to ERP (if using)
   - Update `Cutter inventory by inventory dimension` sheet
   - Adjust transactions if variances found

**Data Created:**
- Transaction log (every addition/subtraction)
- PO tracking records
- BOM requirement calculations
- Inventory summary snapshots (saved with date in filename)

---

### Process 3: Purchase Order Lifecycle

**Steps:**

1. **Create PO**
   - Identify need (cutter shortage, consumable low stock)
   - Create PO with supplier
   - Enter in `PO Customs` sheet: PO#, Date, Items, Ordered Qty, Descriptions, MN

2. **Order Confirmation**
   - Supplier confirms
   - Update Expected Delivery Date

3. **Shipment**
   - Supplier ships
   - Update: AWB No, Shipping Date, ETA Date

4. **Customs Clearance**
   - Items arrive at port
   - Update: Clearance ETA

5. **Receive**
   - Items cleared and delivered
   - Update: Recd Date, GRN NO
   - Post to ERP: ERP GRN

6. **Inventory Update**
   - Add transactions in `Cutters Consumption Updates` or consumables log
   - Update status to "CLOSED"

---

## Data Model Insights

### Entities and Relationships

Based on Excel analysis, the following database entities are needed:

#### Core Entities

1. **Bit (SerialUnit)**
   - `id` (PK)
   - `base_serial_number` (VARCHAR, unique for new bits)
   - `size` (VARCHAR, e.g., "6 1/8\", "8.5\", "12 1/4\"")
   - `type` (VARCHAR, e.g., "FMD44", "GT65RHs")
   - `mat_level` (VARCHAR, e.g., "L3", "L4", "L5")
   - `original_mat_number` (FK to BitDesign)
   - `customer_id` (FK to Customer)
   - `date_manufactured` (DATE)
   - `current_location` (VARCHAR)
   - `current_status` (FK to Status lookup)

2. **BitRepair (RepairJob)**
   - `id` (PK)
   - `bit_id` (FK to Bit)
   - `repair_revision` (INT, e.g., 0 for new, 1 for R1, 2 for R2)
   - `work_order_number` (VARCHAR, unique, e.g., "2025-ARDT-LV4-015")
   - `date_received` (DATE)
   - `source_location` (VARCHAR, e.g., "ARDT-LV4", "LSTK", "SAUDI ARAMCO")
   - `mat_design_id` (FK to BitDesign, can differ from original if redesigned)
   - `new_type` (VARCHAR, if converted to new type)
   - `evaluated_by_user_id` (FK to User)
   - `qc_by_user_id` (FK to User)
   - `date_of_evaluation` (DATE)
   - `reviewed_by_user_id` (FK to User)
   - `date_of_review` (DATE)
   - `approved_by_user_id` (FK to User)
   - `approval_date` (DATE)
   - `disposition` (VARCHAR, e.g., "Repair", "Scrap", "Rerun")
   - `accomplished_date` (DATE)
   - `remarks` (TEXT)
   - `job_name` (VARCHAR)
   - `issues_report` (TEXT)
   - `pdc_production_days` (INT)
   - `erp_item_number` (VARCHAR)
   - `erp_production_order_number` (VARCHAR)

3. **BitDesign (MAT Master)**
   - `id` (PK)
   - `mat_number` (VARCHAR, e.g., "1267829", "1267829M")
   - `revision` (VARCHAR, e.g., "M", "A", "B")
   - `size` (VARCHAR)
   - `type` (VARCHAR)
   - `level` (VARCHAR, "L3", "L4", "L5")
   - `description` (TEXT)
   - `is_active` (BOOLEAN)
   - `superseded_by_id` (FK to BitDesign, for obsolescence)

4. **BOM (Bill of Materials)**
   - `id` (PK)
   - `bit_design_id` (FK to BitDesign)
   - `line_number` (INT)
   - `cutter_id` (FK to Cutter)
   - `quantity` (INT)
   - `is_primary` (BOOLEAN, vs backup)
   - `position_type` (VARCHAR, e.g., "ID", "Cone", "Nose", "Shoulder", "Gauge")

5. **CutterMap (Blade x Pocket Layout)**
   - `id` (PK)
   - `bit_design_id` (FK to BitDesign)
   - `blade_number` (INT, 1-12)
   - `pocket_number` (INT, 1-34+)
   - `cutter_id` (FK to Cutter)
   - `is_primary` (BOOLEAN)
   - `color_code` (VARCHAR, for visual grouping)

6. **EvaluationRecord**
   - `id` (PK)
   - `repair_job_id` (FK to BitRepair)
   - `blade_number` (INT)
   - `pocket_number` (INT)
   - `evaluation_symbol` (VARCHAR, "X", "O", "R", "S", "L", "V", "P", "I", "B")
   - `remarks` (TEXT)

7. **Cutter (Cutter Master)**
   - `id` (PK)
   - `sap_number` (VARCHAR, unique, e.g., "802065")
   - `type` (VARCHAR, e.g., "Round", "IA-STL", "Shyfter")
   - `size` (VARCHAR, e.g., "1313", "13MM Long", "1613")
   - `grade` (VARCHAR, e.g., "CT97", "ELITE RC", "M1")
   - `chamfer` (VARCHAR, e.g., "0.010\"", "0.018\"")
   - `description` (TEXT)
   - `category` (VARCHAR, e.g., "P-Premium", "B-Standard", "S-Super Premium")
   - `is_obsolete` (BOOLEAN)
   - `replacement_cutter_id` (FK to Cutter)

8. **CutterOwnershipCategory**
   - `id` (PK)
   - `name` (VARCHAR, "ENO As New", "ENO Ground", "ARDT Reclaim", "LSTK Reclaim", "New Stock", "Retrofit")
   - `priority` (INT, for consumption order)

9. **CutterTransaction**
   - `id` (PK)
   - `date` (DATE)
   - `cutter_id` (FK to Cutter)
   - `ownership_category_id` (FK to CutterOwnershipCategory)
   - `addition_qty` (INT)
   - `subtraction_qty` (INT)
   - `reference_type` (VARCHAR, "PO", "RepairJob", "Reclaim", "Adjustment")
   - `reference_id` (INT, polymorphic FK)
   - `description` (TEXT)
   - `created_by_user_id` (FK to User)
   - `created_at` (TIMESTAMP)

10. **CutterPurchaseOrder**
    - `id` (PK)
    - `po_number` (VARCHAR, unique)
    - `po_date` (DATE)
    - `supplier_id` (FK to Supplier)
    - `status` (VARCHAR, "OPEN", "IN TRANSIT", "RECEIVED", "CLOSED")
    - `expected_delivery_date` (DATE)

11. **CutterPurchaseOrderLine**
    - `id` (PK)
    - `po_id` (FK to CutterPurchaseOrder)
    - `line_number` (INT)
    - `cutter_id` (FK to Cutter)
    - `ordered_qty` (INT)
    - `received_qty` (INT)
    - `unit_price` (DECIMAL)

12. **ProcessStep (Router)**
    - `id` (PK)
    - `repair_job_id` (FK to BitRepair)
    - `step_number` (INT)
    - `description` (VARCHAR, e.g., "Nozzle Removal", "Sand Blasting")
    - `completed_date` (DATE)
    - `completed_time` (TIME)
    - `operator_user_id` (FK to User)
    - `remarks` (TEXT)

13. **QCChecklist**
    - `id` (PK)
    - `repair_job_id` (FK to BitRepair)
    - `checklist_type` (VARCHAR, "Evaluation", "API Thread", "Die Check")
    - `item_number` (INT)
    - `item_description` (VARCHAR)
    - `result` (VARCHAR, "OK", "Not OK")
    - `remarks` (TEXT)

14. **Quotation**
    - `id` (PK)
    - `repair_job_id` (FK to BitRepair)
    - `customer_id` (FK to Customer)
    - `quotation_date` (DATE)
    - `total_cutter_cost` (DECIMAL)
    - `total_labor_cost` (DECIMAL)
    - `total_material_cost` (DECIMAL)
    - `overhead_rate` (DECIMAL)
    - `margin_rate` (DECIMAL)
    - `total_amount` (DECIMAL)
    - `status` (VARCHAR, "Draft", "Sent", "Approved", "Rejected")
    - `approved_date` (DATE)

15. **QuotationLine**
    - `id` (PK)
    - `quotation_id` (FK to Quotation)
    - `line_type` (VARCHAR, "Cutter", "Labor", "Material")
    - `description` (VARCHAR)
    - `quantity` (INT)
    - `unit_price` (DECIMAL)
    - `line_amount` (DECIMAL)

16. **TechnicalInstruction**
    - `id` (PK)
    - `applies_to_type` (VARCHAR, "SerialNumber", "MATNumber", "BitType", "Customer")
    - `applies_to_value` (VARCHAR)
    - `instruction_text` (TEXT)
    - `is_active` (BOOLEAN)

17. **Customer**
    - `id` (PK)
    - `name` (VARCHAR, "LSTK", "SAUDI ARAMCO", "Halliburton")
    - `short_code` (VARCHAR, "LSTK", "ARAMCO", "HAL")
    - `contract_number` (VARCHAR)
    - `contact_info` (TEXT)

18. **Supplier**
    - `id` (PK)
    - `name` (VARCHAR)
    - `contact_info` (TEXT)

19. **Consumable**
    - `id` (PK)
    - `item_number` (VARCHAR, e.g., "FS-0678", "CN-000208")
    - `product_name` (VARCHAR)
    - `search_name` (VARCHAR)
    - `product_type` (VARCHAR, "Item", "Service")
    - `inventory_unit` (VARCHAR, "EA", "Kilogram")
    - `item_model_group` (VARCHAR, "PhyInv")
    - `storage_dimension_group` (VARCHAR, "SWL")
    - `quarterly_consumption` (INT)
    - `minimum_buffer_stock` (INT)
    - `image_url` (VARCHAR)

---

### Relationships

- **Bit** 1:N **BitRepair** (one bit can have multiple repair jobs: R0, R1, R2...)
- **BitRepair** 1:N **EvaluationRecord** (one repair has many cutter evaluations)
- **BitRepair** 1:N **ProcessStep** (one repair has many process steps)
- **BitRepair** 1:N **QCChecklist** (one repair has many checklist items)
- **BitRepair** 1:1 **Quotation** (one repair has one quotation)
- **Quotation** 1:N **QuotationLine** (one quotation has many line items)
- **BitDesign** 1:N **BOM** (one design has many BOM lines)
- **BitDesign** 1:N **CutterMap** (one design has many cutter positions)
- **Cutter** 1:N **BOM** (one cutter type appears in many BOMs)
- **Cutter** 1:N **CutterMap** (one cutter type appears in many map positions)
- **Cutter** 1:N **CutterTransaction** (one cutter has many transactions)
- **CutterPurchaseOrder** 1:N **CutterPurchaseOrderLine**
- **CutterPurchaseOrderLine** N:1 **Cutter**

---

## Legacy Patterns to Avoid

### Pattern 1: Serial Number + Repair Revision in One Field

**Excel Pattern:**
- Stores `12721812R2` as single text field
- Requires text parsing to extract base SN and revision

**Problems:**
- Can't easily query "all R2 repairs"
- Can't enforce format consistency
- Can't validate that base SN exists
- Can't use as foreign key

**DB Solution:**
- Separate fields: `bit.base_serial_number` and `bit_repair.repair_revision`
- Composite unique key: `(bit_id, repair_revision)`
- Easy queries: `WHERE repair_revision = 2`

---

### Pattern 2: Formula-Driven Status

**Excel Pattern:**
- Status calculated by formula: `=IF('Eval-LSTK'!D57<>"","Repair Date",IF('Eval-LSTK'!D59<>"","Scrap Date","Rerun Date"))`

**Problems:**
- Status not explicitly stored
- Fragile (formula can break)
- Can't filter/index on status efficiently

**DB Solution:**
- Explicit `bit_repair.disposition` field (VARCHAR or FK to lookup)
- Set by business logic in application code
- Update when evaluation decision is made
- Indexed for fast queries

---

### Pattern 3: Cutter Map in Wide Grid (196 columns)

**Excel Pattern:**
- Columns BR through column ~HL store cutter evaluation symbols
- Each column = one pocket position
- Each row (32+) = one blade

**Problems:**
- Fixed maximum positions (can't support bits with more pockets)
- Sparse data (many empty cells)
- Hard to query "all pockets with X symbol"
- Can't easily add metadata per pocket

**DB Solution:**
- Normalized table: `evaluation_record(repair_job_id, blade_number, pocket_number, symbol, remarks)`
- Variable number of pockets per bit
- Easy queries: `WHERE symbol = 'X'`
- Easy to add columns like `cutter_removed_date`, `replaced_with_cutter_id`

---

### Pattern 4: Cross-Sheet Formula Dependencies

**Excel Pattern:**
- `Data` sheet pulls from `Eval-LSTK`, `ARDT Cutter Entry`, `Eng. Cutter Entry`, `Quotation`, etc.
- Circular references prevented by careful formula design
- Very fragile

**Problems:**
- Breaking change if sheet renamed or row/column inserted
- Difficult to trace data flow
- No transaction integrity
- Formulas recalculate on every change (slow)

**DB Solution:**
- Foreign keys and joins
- Database constraints ensure referential integrity
- Indexed joins are fast
- Triggers or application code handle calculated fields
- Materialized views for complex aggregations

---

### Pattern 5: Manual File and Folder Naming

**Excel Pattern:**
- Job card file manually named: `YYYY-SOURCE-MAT-REVISION-SN.xlsx`
- Folder manually created with same name
- User must type correctly

**Problems:**
- Typos lead to misnamed files
- Hard to find files (must remember naming convention)
- Can't enforce uniqueness (can accidentally create duplicate)
- No auto-linking between tracking sheet and job card file

**DB Solution:**
- Work order number auto-generated by database sequence
- Files uploaded to storage with UUID or auto-incremented ID
- `repair_job.work_order_number` stored in DB
- `repair_job.job_card_file_path` points to file storage location
- UI auto-generates folder structure
- Search by any field (SN, MAT, customer, date)

---

### Pattern 6: Free-Text Status Values

**Excel Pattern:**
- Status field allows any text: "Repair", "Repairs", "In Repair", "repair", "HOLD", "Hold", "hold"

**Problems:**
- Inconsistent capitalization
- Typos create phantom statuses
- Can't reliably count bits in each status
- No workflow enforcement

**DB Solution:**
- `status` table with predefined values
- Foreign key constraint: `bit_repair.status_id` references `status.id`
- Dropdown in UI shows only valid statuses
- Can add `status_order` for workflow sequence
- Can add `allowed_transitions` for state machine

---

### Pattern 7: Inventory Balance as Formula

**Excel Pattern:**
- Current balance calculated by SUMIFS across transaction log

**Problems:**
- Recalculates every time sheet opens (slow for large data)
- Calculation overhead on every transaction entry
- No historical snapshots (can't see "balance as of 2025-01-01")

**DB Solution (Hybrid Approach):**
1. **Transaction log table** (source of truth)
2. **Inventory summary table** (current balances)
   - Updated by trigger on transaction insert/update
   - OR updated by nightly scheduled job
3. **Inventory history table** (snapshots)
   - Daily/weekly snapshot of balances for historical reporting

---

### Pattern 8: Hardcoded Prices and Rates in Formulas

**Excel Pattern:**
- Cutter prices hardcoded in Quotation sheet formulas
- Labor rates hardcoded

**Problems:**
- Price changes require formula editing
- No price history (can't quote old job at old prices)
- No multi-currency support

**DB Solution:**
- `cutter_price_history(cutter_id, effective_date, unit_price, currency)`
- `labor_rate_history(process_step, effective_date, hourly_rate, currency)`
- Quotation references prices effective as of quotation date
- Price changes don't affect historical quotations

---

### Pattern 9: BOM Requirement Calculation in Excel

**Excel Pattern:**
- `L3&L4 BOMs & Cutters` sheet uses VLOOKUP/XLOOKUP to match bits to BOMs
- Sums cutter quantities across all active bits

**Problems:**
- Formula-intensive
- Requires manual refresh
- Can't filter "BOM requirement for bits received this month"
- No drill-down to see which bits need this cutter

**DB Solution:**
- Query:
  ```sql
  SELECT
      c.sap_number,
      c.description,
      SUM(b.quantity) AS total_qty_needed
  FROM bit_repair br
  JOIN bit_design bd ON br.mat_design_id = bd.id
  JOIN bom b ON bd.id = b.bit_design_id
  JOIN cutter c ON b.cutter_id = c.id
  WHERE br.status_id IN (SELECT id FROM status WHERE is_in_production = TRUE)
  GROUP BY c.id
  ```
- Materialized view refreshed hourly
- Drill-down: join back to `bit_repair` to see which bits
- Filter by date, customer, location easily

---

### Pattern 10: No Audit Trail

**Excel Pattern:**
- Cells can be edited and overwritten
- No record of who changed what when

**Problems:**
- Can't investigate "Why was this cutter quantity changed?"
- Can't rollback accidental edits
- No accountability

**DB Solution:**
- Every table has: `created_by_user_id`, `created_at`, `updated_by_user_id`, `updated_at`
- Optional: audit trail table logs every change (old value, new value, user, timestamp)
- Soft delete: `is_deleted` flag instead of hard delete
- Version control for critical records (e.g., BOM revisions)

---


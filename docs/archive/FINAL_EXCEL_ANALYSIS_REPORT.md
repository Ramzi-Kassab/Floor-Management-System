# Excel Workbooks Analysis Report
## PDC Bit Manufacturing & Repair Management System

**Analysis Date:** 2025-11-18
**Project:** Floor Management System - B
**Purpose:** Analyze existing Excel workflows to design Django/PostgreSQL implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Workbook Inventory](#workbook-inventory)
3. [Workbook-by-Workbook Analysis](#workbook-by-workbook-analysis)
4. [Key Business Processes Identified](#key-business-processes-identified)
5. [Data Model Insights](#data-model-insights)
6. [Legacy Patterns to Avoid](#legacy-patterns-to-avoid)
7. [Integration Points and Dependencies](#integration-points-and-dependencies)
8. [Sample Data Patterns](#sample-data-patterns)
9. [Implementation Prompt](#implementation-prompt)

---

## Executive Summary

### Scope of Analysis

Six Excel workbooks were analyzed containing the core business logic for:
- PDC bit repair and evaluation job cards
- Bit lifecycle tracking across customers and repair cycles
- Cutter inventory management (availability, consumption, forecasting)
- Purchase order tracking for cutters and consumables
- Consumables and spare parts inventory for ERP migration

### Key Findings

1. **Job Card Template** (27 sheets): Comprehensive multi-sheet workbook acting as the "control center" for each repair job
   - Master data drives all sub-sheets via complex formulas
   - Supports multiple customer-specific evaluation forms (LSTK, ARAMCO, Halliburton)
   - Cutter evaluation grid uses blade x pocket matrix structure
   - Cross-sheet dependencies create fragile but powerful automation

2. **Bits Tracking** (26 sheets): Master register of all bits ever received
   - Over 1 million rows of historical data
   - Tracks serial numbers with repair revision appended (e.g., `12721812R2`)
   - Multiple customer-specific tracking sheets (ARAMCO, LSTK, HALLIBURTON, etc.)
   - Status tracking through workflow stages

3. **Cutter Inventory** (20 sheets): Complex availability forecasting system
   - Tracks multiple ownership categories: ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock
   - Real-time consumption tracking (6-month, 3-month, 2-month windows)
   - Safety stock calculations with tiered buffer logic
   - BOM requirement forecasting based on bits in production

4. **PO Tracking** (2 sheets): Purchase order lifecycle management
   - Tracks items from order through customs, shipping, receiving, GRN
   - Formula-driven status calculations
   - Links to MN (Material Number) for ERP integration

5. **Consumables** (6 sheets): ERP-ready consumables and spare parts catalog
   - Structured for Microsoft Dynamics integration
   - Product dimensions (configurations, sizes, colors, styles)
   - Inventory behavior specifications (PhyInv, SWL)

6. **ERP Reconciliation** (6 sheets): Inventory reconciliation between physical count and ERP system
   - Comparison of ENO, NEW, RCLM, RCLM-ARDT categories
   - Variance detection and correction tracking

### Critical Observations

**Strengths of Current System:**
- Comprehensive coverage of business processes
- Rich formula-based automation
- Customer-specific form generation
- Historical data preservation

**Limitations/Risks:**
- No multi-user concurrency (file locking)
- No audit trail (who changed what, when)
- Fragile formula dependencies (easy to break)
- Data duplication across workbooks
- Manual synchronization required
- No validation enforcement
- Poor searchability and reporting
- Version control issues

---

## Workbook Inventory

| # | Workbook Name | Sheets | Purpose | Key Data |
|---|--------------|--------|---------|----------|
| 1 | `2025-ARDT-LV4-015-14204328.xlsx` | 27 | Job card template for single bit repair | Bit ID, Evaluation grid, Quotation, Instructions, Checklists |
| 2 | `Copy of BITS TRACKING 7-6-2025.xlsx` | 26 | Master bit lifecycle tracking | Serial numbers, repair history, status, customer |
| 3 | `Copy of Cutter Inventory 11-18-2025.xlsx` | 20 | Cutter availability and forecasting | Stock levels, consumption, BOM requirements, orders |
| 4 | `Cutter inventory by inventory dimension-Oct-2025.xlsx` | 6 | ERP vs physical inventory reconciliation | ERP dimensions, variance analysis |
| 5 | `new version of PO Customs- updated.xlsx` | 2 | Purchase order tracking | PO, items, quantities, shipping, customs, GRN |
| 6 | `Consumables and Spare Parts-PDC 11-4-2025.xlsx` | 6 | Consumables catalog for ERP | Item numbers, product types, specs, dimensions |

**Total:** 6 workbooks, 87 sheets, millions of data rows

---

## Workbook-by-Workbook Analysis

### 1. Job Card Template: `2025-ARDT-LV4-015-14204328.xlsx`

#### Overview

**File:** `2025-ARDT-LV4-015-14204328.xlsx`
**Sheets:** 27
**Purpose:** Comprehensive job card for a single PDC bit repair/rerun/scrap evaluation

**Sheet List:**
1. `Data` - Master control sheet
2. `TRANSPOSE` - Cutter map transpose helper (named ranges for BLADE1-12)
3. `ARDT Cutter Entry` - ARDT technician cutter evaluation
4. `Eng. Cutter Entry` - Engineering-approved cutter changes
5. `Evaluation` - Internal evaluation form
6. `E checklist` - Evaluation quality checklist
7. `Router Sheet` - Process routing and workflow tracking
8. `LPT Report` - Leak pressure test report
9. `Evaluation (2)` - Alternative evaluation layout
10. `Instructions` - Technical instructions lookup table
11. `Eval-LSTK` - LSTK customer evaluation form
12. `Eval-LSTK (2)` - Alternative LSTK layout
13. `Quotation` - Cost quotation calculator
14. `Qut. HALL.` - Halliburton quotation
15. `Rework Cutter Entry` - Rework-specific cutter tracking
16. `Rework` - Rework operations data
17. `Rework (2)` - Alternative rework layout
18. `Die Check Entry` - NDT die check results
19. `Delivery Tkt` - Delivery ticket
20. `Eval & Quot-AR` - ARAMCO evaluation and quotation (combined)
21. `API Thread Inspection` - API thread inspection checklist
22. `Brazing` - Brazing operation tracking
23. `Hardfacing & Build up` - Hardfacing/matrix build-up tracking
24. `Cutters LPT Report-not complete` - Cutter-specific LPT (incomplete)
25. `L3 bit material consume` - L3 material consumption
26. `Sheet1` - Unused/scratch
27. `ARAMCO-CONTRACT-6600048646` - ARAMCO contract-specific form

---

#### Sheet: `Data` (Master Control Center)

**Dimensions:** 1999 rows × 196 columns

**Purpose:**
The `Data` sheet is the **central nervous system** of the job card. All other sheets pull data from here via formulas. User enters key information in columns A-B, and formulas cascade throughout the workbook.

**Key Fields (Columns A-B, Rows 1-20):**

| Row | Field | Example Value | Type |
|-----|-------|---------------|------|
| 1 | ARDT Work Order No | `2025-ARDT-LV4-015` | Manual entry |
| 2 | Serial Number | `14204328` | Manual entry |
| 3 | Size | `8.5` | Manual entry |
| 4 | Type | `GT65RHs` | Manual entry |
| 5 | LV5 Mat # | `1267829M` | Manual entry (triggers BOM lookup) |
| 6 | Bit Date Received (MM/DD/YYYY) | `2025-01-16` | Manual entry |
| 7 | From | `ARDT-LV4` | Manual entry (customer/source) |
| 8 | LV3 or LV4 Mat # | `1158011` | Manual entry |
| 9 | LV3 or LV4 Remark | `BOM, Might be changed, waiting Saad.` | Manual entry |
| 10 | New Type | (blank) | Manual entry |
| 11 | Evaluated by | (blank) | Manual entry |
| 12 | QC By | (blank) | Manual entry |
| 13 | Date of Evaluation (MM/DD/YYYY) | (blank) | Manual entry |
| 14 | [Dynamic label] | Formula-driven | Formula based on customer |
| 15 | Date of Review (MM/DD/YYYY) | (blank) | Manual entry |
| 16 | Requested by | Formula `=IF(B7<>"",B7,"")` | Pulled from "From" |
| 17 | Department head | `Ramzi` | Manual entry |
| 18 | [Dynamic date label] | Formula-driven (Repair/Scrap/Rerun Date) | Formula based on Eval-LSTK status |
| 19 | Approved by | (blank) | Manual entry |
| 20 | Approval Date | (blank) | Manual entry |

**Cutter Evaluation Grid Storage (Columns BR onwards):**

The actual cutter-by-cutter evaluation data (X, O, S, R, L, V, P, I, B symbols) is stored starting from column BR (row 32 onwards). This is a **blade x pocket matrix**:
- **Rows:** Represent blades (Blade 1, Blade 2, ..., Blade 12)
- **Columns:** Represent pocket positions on each blade (innermost to gauge)

**Named Ranges for Blade Data:**
- `BLADE1` → `TRANSPOSE!$C$4:$AJ$4`
- `BLADE2` → `TRANSPOSE!$C$5:$AJ$5`
- ...
- `BLADE12` → `TRANSPOSE!$C$15:$AJ$15`

These named ranges are used by evaluation sheets to pull cutter positions dynamically.

**Cross-Sheet Formula Dependencies:**

The `Data` sheet contains formulas that reference:
- `Instructions` sheet (to check for special flags like "WFD")
- `ARDT Cutter Entry` sheet (to sum cutter quantities)
- `Eng. Cutter Entry` sheet (to check engineering approval)
- `Eval-LSTK` sheet (to determine repair vs scrap vs rerun)
- `Quotation` sheet (to pull pricing)
- `Rework` sheet (to add rework cutter quantities)

**Example Cross-Sheet Formulas:**

```excel
// Row 2, Col C: Check if "WFD" flag is present
=IF(COUNTIF(Instructions!$L$1,"*WFD*"),"WFD","")

// Row 12, Col E: Sum cutter quantities from multiple sheets
=IF('Eng. Cutter Entry'!C4<>"",
   IF($L$9<>1,
      ('ARDT Cutter Entry'!AQ$58 + 'ARDT Cutter Entry'!AQ$59 + 'ARDT Cutter Entry'!AQ$60 + 'ARDT Cutter Entry'!AQ$61),
      'ARDT Cutter Entry'!AQ$58 + 'ARDT Cutter Entry'!AQ$59 + 'ARDT Cutter Entry'!AQ$60 + 'ARDT Cutter Entry'!AQ$61 + Rework!C73
   ),
   'ARDT Cutter Entry'!AQ2 + 'ARDT Cutter Entry'!AQ3 + 'ARDT Cutter Entry'!AQ4 + 'ARDT Cutter Entry'!AQ5
)

// Row 18, Col A: Dynamic label based on Eval-LSTK status
=IF('Eval-LSTK'!D57<>"","Repair Date",IF('Eval-LSTK'!D59<>"","Scrap Date","Rerun Date"))
```

**Business Logic:**

1. **User enters bit identification** (SN, Size, Type, LV5 MAT, Date, From)
2. **LV5 MAT lookup** triggers:
   - BOM lookup (from external BOM database/sheet)
   - Cutter map generation (blade x pocket layout)
   - Prefill of cutter part numbers in evaluation grids
3. **Evaluation data entry** (ARDT techs mark cutters with X, O, R, S, etc.)
4. **Engineering review** (Engineer approves/modifies cutter replacements)
5. **Quotation generation** (auto-calculated based on cutter quantities, labor, parts)
6. **Customer-specific forms** (LSTK, ARAMCO, Halliburton) auto-populate
7. **Print/PDF export** for delivery to customer

---

#### Sheet: `Evaluation` (Internal Cutter Evaluation Grid)

**Dimensions:** 62 rows × 34 columns

**Purpose:**
Grid-based cutter evaluation form where evaluator visually inspects each cutter and marks its condition.

**Evaluation Symbols:**
- `X` = Needs to be replaced
- `O` = Okay (reusable)
- `R` = Needs to be rotated
- `S` = Special (custom meaning)
- `L` = Lost cutter
- `V` = Fin surrounding needs build-up
- `P` = Pocket needs build-up
- `I` = Impact arrestor needs build-up
- `B` = Body condition issue

**Grid Structure:**

- **Row 16:** Cutter position numbers (pulled from Data sheet columns BR, BS, BT, etc.)
- **Row 17-26+:** Blade numbers (1, 2, 3, ..., 12)
- **Grid cells:** Formulas that reference `Data!BR32`, `Data!BS32`, etc. to display evaluation symbols

**Instructions (Row 11):**

> "Clearly mark the # 1 blade with permanent marker or pen; Begin with the inner most cutter on the blade, mark each cutter with X if needs to be replaced, R if needs to be rotated, and O if okay. Then go for the next blade in a clockwise direction and do the same. And P if pocket needs to build up, I if Impact Arrestor needs to build up, V surrounding the fin needs to build up. After checking and marking cutters through all the blades, transfer Xs, Rs and Os to the Table below."

**Data Flow:**

1. Evaluator physically inspects bit and marks symbols on `Data` sheet (columns BR onwards)
2. `Evaluation` sheet formulas pull symbols from `Data`
3. Symbols render in printable grid layout for documentation

**Formula Example (Row 17, Col C):**

```excel
=IF(Data!$L$9=1, Data!BR32, "")
```

This pulls the evaluation symbol from Data!BR32 if certain conditions are met (controlled by Data!$L$9 flag).

---

#### Sheet: `ARDT Cutter Entry` (ARDT Technician Cutter Replacement Tracking)

**Dimensions:** 461 rows × 63 columns

**Purpose:**
Technician enters "X" marks for cutters that ARDT plans to replace. This sheet calculates total quantities needed for each cutter part number.

**Grid Structure:**

- **Row 2:** Header: "Cutter's number from ID to Gauge area"
- **Row 3:** Cutter position numbers (formulas from Data sheet)
- **Row 4-15:** Blade numbers (1-12)
- **Grid cells:** User enters `X` manually for cutters to replace

**Example Data (Rows 4-9):**

| Blade | Pos 1 | Pos 2 | Pos 3 | Pos 4 | Pos 5 | Pos 6 | Pos 7 | Pos 8 |
|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| 1     | X     | X     | X     | X     | X     | X     | X     | X     |
| 2     | X     | X     | X     | X     | X     |       |       |       |
| 3     | X     | X     | X     | X     | X     | X     | X     |       |
| 4     | X     | X     | X     | X     | X     |       |       |       |
| 5     | X     | X     | X     | X     | X     | X     | X     |       |
| 6     | X     | X     | X     | X     | X     |       |       |       |

**Summary Calculations (Rows 58-61+):**

Formulas sum up how many of each cutter part number are needed across all blades. These totals are referenced by the `Data` sheet and `Quotation` sheet.

**Formula Example (Row 58, Col AQ):**

```excel
=COUNTIF(C4:C15, "X")  // Count X marks in column C (position 1)
```

---

#### Sheet: `Eng. Cutter Entry` (Engineering-Approved Cutter Changes)

**Dimensions:** 39 rows × 54 columns

**Purpose:**
Engineer reviews ARDT recommendations and may modify cutter replacements. This sheet overrides ARDT entry.

**Structure:** Identical to `ARDT Cutter Entry` but typically starts blank.

**Business Logic:**

If `Eng. Cutter Entry` has data, it takes precedence over `ARDT Cutter Entry` in quotation and material consumption calculations (see Data sheet formula examples above).

---

#### Sheet: `Eval-LSTK` (LSTK Customer Evaluation Form)

**Dimensions:** 62 rows × 27 columns

**Purpose:**
Customer-specific evaluation form for LSTK. Layout similar to internal `Evaluation` sheet but with LSTK branding and specific fields.

**Key Fields:**
- Work Order No (formula from Data!B1)
- Size (formula from Data!B3)
- Type (formula from Data!B4)
- Cutter grid (formulas pulling from Data sheet columns BR onwards)

**Conditional Display Logic:**

Cutter grid cells use formulas like:

```excel
=IF(OR(Data!BR32="X", Data!BR32="R", Data!BR32="O"), Data!BR32, "")
```

This only shows X, R, O symbols (hiding other internal symbols like P, I, V, B, L, S).

**Decision Fields (Rows 57, 59):**

- Row 57: Repair Date
- Row 59: Scrap Date

These fields control the dynamic label in `Data` sheet Row 18 (Repair Date vs Scrap Date vs Rerun Date).

---

#### Sheet: `Eval & Quot-AR` (ARAMCO Evaluation & Quotation)

**Dimensions:** 70 rows × 57 columns

**Purpose:**
Combined evaluation and quotation form for ARAMCO customer (Saudi Aramco). Single-page format for ARAMCO contract requirements.

**Key Features:**
- Old Type vs New Type comparison
- Cutter grid with TRANSPOSE references
- Integrated quotation section
- Contract-specific headers and footers

**Formula Example (Row 16, Col C):**

```excel
=TRIM(IF(TRANSPOSE!$C$4<>"", TRANSPOSE!$C$4, ""))
```

Uses TRANSPOSE sheet to rotate blade/pocket data for different layout orientation.

---

#### Sheet: `Instructions` (Technical Instructions Lookup)

**Dimensions:** 320 rows × 22 columns

**Purpose:**
Lookup table of special instructions for specific serial numbers, MAT numbers, or bit types.

**Columns:**
- `ORDER NO.` (Work order number)
- `SEREAL NO.` (Serial number)
- `SIZE`
- `TYPE`
- `LV5 MAT NO.`
- `FROM` (Customer)
- `LV3 or LV4 MAT NO.`
- `Cutters` (Special cutter instructions)
- `REMARKS`
- `Instruction` (Free-text technical instructions)

**Example Instructions:**

| SN | MAT | From | Instruction |
|----|-----|------|-------------|
| 14081145 | 1257458 | | `Saad 12/11/2023...` |
| 13824396 | | | `WFD` (White Finger Design) |
| | 1092981 | ARDT-LV4 | `Full gauge pad relief...` |

**Usage in `Data` Sheet:**

```excel
// Row 2, Col C
=IF(COUNTIF(Instructions!$L$1,"*WFD*"),"WFD","")
```

This checks if current bit has "WFD" instruction and displays flag.

---

#### Sheet: `Router Sheet` (Process Routing)

**Dimensions:** 61 rows × 10 columns

**Purpose:**
Workflow tracking sheet documenting each process step, date, time, and operator signature.

**Process Steps (Rows 11-40+):**

1. Nozzle Removal
2. Cerebro Removal
3. Cer.O-Ring Removal
4. Washing
5. Sand Blasting
6. Pressure Test
7. Die Check
8. Photos & Evaluation
9. Bit Head Preparation
10. De-Brazing (If required)
... (continues for ~30 steps)

**Columns:**
- Step number
- Description
- Date (formula-driven or manual)
- Time Receipt
- Operator Sign
- Remarks

**Formulas:** Pull bit identification from `Data` sheet (Work Order No, Serial No, Size, Type, From).

---

#### Sheet: `E checklist` (Evaluation Quality Checklist)

**Dimensions:** 31 rows × 22 columns

**Purpose:**
QC checklist for evaluation quality control.

**Checklist Items (Rows 11-30+):**

| Sr. No | Evaluation Step | OK | Not OK | Remarks |
|--------|-----------------|----|----|---------|
| 1 | Bit Cleanliness | [ ] | [ ] | |
| 2 | Paperwork | [ ] | [ ] | |
| 3 | Bit Stamping | [ ] | [ ] | |
| 4 | Die Check | [ ] | [ ] | |
| 5 | Ring Gauge (Go) | [ ] | [ ] | |
| 6 | Ring Gauge (No Go) | [ ] | [ ] | |
| 7 | Nozzle BoreLine | [ ] | [ ] | |
| 8 | Nozzle Threads | [ ] | [ ] | |
| 9 | Apex | [ ] | [ ] | |
| 10 | Junk Slot | [ ] | [ ] | |
... (continues)

---

#### Sheet: `API Thread Inspection`

**Dimensions:** 41 rows × 35 columns

**Purpose:**
API thread inspection checklist with measurements and go/no-go checks.

**Inspection Points:**
- Pin face
- Thread
- Pitch gauge
- Mud seal
- Pin height
- Thread repair requirements

---

#### Sheet: `Die Check Entry`

**Dimensions:** 38 rows × 36 columns

**Purpose:**
NDT (Non-Destructive Testing) die check results entry in blade x pocket grid format.

**Structure:** Similar to evaluation grid - technician marks cracks or defects detected by die check.

---

#### Sheet: `Quotation`

**Dimensions:** 66 rows × 40 columns

**Purpose:**
Cost quotation calculator that sums:
- Cutter replacement costs (quantity × unit price)
- Labor costs (process steps × rates)
- Material costs (consumables)
- Overhead and margin

**Formula-Driven Pricing:**

Pulls cutter quantities from `ARDT Cutter Entry` or `Eng. Cutter Entry` and multiplies by price list (likely from external sheet or hardcoded).

---

#### Sheets: `Rework`, `Rework (2)`, `Rework Cutter Entry`

**Purpose:**
Rework-specific tracking when a bit fails inspection after repair and requires additional work.

**Additional Cutter Quantities:**

Rework sheets add incremental cutter quantities to the base ARDT/Eng quantities (see Data sheet formula examples with `Rework!C73`).

---

#### Sheet: `TRANSPOSE`

**Dimensions:** Not analyzed in detail

**Purpose:**
Helper sheet for transposing blade/pocket data for different layout orientations in customer-specific forms.

**Named Ranges:**

Defines `BLADE1` through `BLADE12` and `TRANS2B1` through `TRANS2B12` for easy reference in formulas.

---

#### Key Insights from Job Card Template

**Strengths:**
- Single source of truth (Data sheet)
- Automated form generation for multiple customers
- Rich calculation logic
- Comprehensive process documentation

**Weaknesses/Legacy Issues:**
- **Extreme formula complexity** - formulas with 5+ nested IFs, cross-sheet references
- **Fragile** - easy to break by inserting rows/columns
- **No concurrent editing** - only one user can work at a time
- **No version history** - changes overwrite without audit
- **Hard to search** - can't easily find all bits with specific status
- **Manual file naming** - folder and file name manually created from data
- **Data duplication** - same bit info repeated in tracking workbook and job card
- **No referential integrity** - can enter invalid MAT numbers, cutter part numbers

**Data to Preserve:**
- Bit identification (SN, Size, Type, MAT)
- Customer information
- Evaluation symbols and grid positions
- Cutter quantities and part numbers
- Process step completion dates and operators
- Quotation breakdown
- Approval chain
- Technical instructions

---

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


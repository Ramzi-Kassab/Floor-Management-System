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


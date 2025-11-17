# Evaluation & Technical Instructions Module

A comprehensive evaluation engine for PDC bit manufacturing and repair operations, providing technical instruction generation, requirements tracking, and complete audit trails.

## Overview

This module provides:
- **Evaluation Engine** - Systematic cutter-by-cutter assessment of PDC bits
- **Technical Instructions** - Rule-based automated instruction generation
- **Requirements Tracking** - Mandatory workflow requirement enforcement
- **Thread & NDT Inspections** - API thread and non-destructive testing records
- **Interactive Grid Editor** - Visual pocket/cutter grid with color-coded evaluations
- **Engineer Review Workflow** - Multi-stage approval process with change highlighting
- **Complete Audit Trail** - Full history of all modifications and approvals

## Domain Context

### PDC Bit Design Levels

PDC (Polycrystalline Diamond Compact) bits use a hierarchical design system:

- **L3 (Level 3)** - Base bit platform/body design
- **L4 (Level 4)** - Cutter layout and geometry specification
- **L5 (Level 5)** - Specific cutter types and materials configuration

### Bit Types

| Code | Name | Description |
|------|------|-------------|
| **HDBS** | High Durability Bit System | Advanced PDC bit design for extended run life |
| **SMI** | Standard Matrix Impregnated | Proven legacy design with field performance |

### MAT Numbers and Revisions

- **MAT Number** - Material number, unique identifier for a specific bit design configuration
- **Revision** - Version control for design changes (e.g., REV A, REV B)
- Example: `MAT-12345-REV-B` indicates design 12345, second revision

### Bit Anatomy

#### Blades and Pockets
- **Blades** - Radial fins extending from bit center, typically numbered 1-7
- **Pockets** - Machined cavities that hold cutters, distributed along blades
- **Cutters** - PDC inserts (polycrystalline diamond on tungsten carbide substrate)
- **Primary Cutter** - Main cutting element at position
- **Secondary Cutter** - Backup/support cutter at same position

#### Bit Sections (Center to Outer Edge)

```
[CENTER] → CONE → NOSE → TAPER → SHOULDER → GAUGE → [OUTER EDGE]
```

| Section | Sequence | Description | Color Code |
|---------|----------|-------------|------------|
| **CONE** | 1 | Center/cone area, first contact with formation | #FF6B6B |
| **NOSE** | 2 | Nose section, primary rock breaking zone | #4ECDC4 |
| **TAPER** | 3 | Tapered transition section | #45B7D1 |
| **SHOULDER** | 4 | Shoulder area, stability zone | #96CEB4 |
| **GAUGE** | 5 | Outer gauge section, borehole diameter control | #FFEAA7 |

### Feature Codes (V/P/I/B)

Feature codes indicate special conditions on bit geometry beyond cutter status:

| Code | Name | Geometry Type | Description | Color |
|------|------|---------------|-------------|-------|
| **V** | Build-Up Fin | FIN | Material build-up on fin/blade geometry | #0000FF |
| **P** | Pocket | POCKET | Damage to cutter pocket affecting stability | #008080 |
| **I** | Impact Arrestor | BODY | Issue with impact arrestor feature | #FF00FF |
| **B** | Body Build-Up | BODY | Material build-up on bit body | #A52A2A |

### Cutter Evaluation Codes (X/O/S/R/L)

Each cutter receives an evaluation code indicating its condition and required action:

| Code | Name | Action | Description | Color |
|------|------|--------|-------------|-------|
| **X** | Damaged-Replace | REPLACE | Broken, chipped PDC table, or thermal damage - needs immediate replacement | #FF0000 (Red) |
| **O** | OK-Good | KEEP | Good condition, no action required | #00FF00 (Green) |
| **S** | Braze Fill | BRAZE_FILL | Pocket requires braze fill repair for cutter stability | #FFA500 (Orange) |
| **R** | Rotate | ROTATE | Can be rotated to expose fresh cutting face | #FFFF00 (Yellow) |
| **L** | Lost | LOST | Cutter missing from pocket, replacement required | #800080 (Purple) |

## Data Model Architecture

### Entity Relationship Overview

```
Reference Tables (Static)
├─ CutterEvaluationCode (X, O, S, R, L)
├─ FeatureCode (V, P, I, B)
├─ BitSection (CONE, NOSE, TAPER, SHOULDER, GAUGE)
└─ BitType (HDBS, SMI)

Core Evaluation Layer
├─ EvaluationSession (per-bit evaluation container)
│   ├─ EvaluationCell[] (per-pocket/cutter entries)
│   ├─ ThreadInspection[] (API thread assessments)
│   ├─ NDTInspection[] (non-destructive testing)
│   └─ EvaluationChangeLog[] (audit trail)
│
├─ TechnicalInstructionInstance[] (generated instructions)
└─ RequirementInstance[] (workflow requirements)

Template Engine Layer
├─ TechnicalInstructionTemplate (rule definitions)
└─ RequirementTemplate (requirement definitions)

Integration Links
├─ → Inventory.SerialUnit (physical bit)
├─ → Inventory.BitDesignRevision (MAT reference)
├─ → Inventory.Item (cutter design)
├─ → Production.JobCard (work order context)
├─ → Production.BatchOrder (customer order)
└─ → HR.HREmployee (evaluator, engineer)
```

### Reference Tables

#### CutterEvaluationCode
Defines standard codes for cutter condition assessment with associated actions and colors.

```python
CutterEvaluationCode:
  - code: "X"              # Single character code
  - name: "Damaged-Replace"
  - description: "Cutter needs immediate replacement..."
  - action: REPLACE        # REPLACE | KEEP | BRAZE_FILL | ROTATE | LOST
  - color_code: "#FF0000"  # Hex color for UI
  - sort_order: 1
  - is_active: True
```

#### FeatureCode
Defines feature markers for special geometric conditions.

```python
FeatureCode:
  - code: "V"              # Feature marker
  - name: "Build-Up Fin"
  - geometry_type: FIN     # FIN | POCKET | BODY | OTHER
  - color_code: "#0000FF"
```

#### BitSection
Defines standard sections of a PDC bit from center to outer edge.

```python
BitSection:
  - code: "CONE"
  - name: "Cone Section"
  - sequence: 1            # Order from center (1) to outer (5)
  - description: "Center area..."
```

#### BitType
Defines bit type classifications and manufacturers.

```python
BitType:
  - code: "HDBS"
  - name: "HDBS Type"
  - manufacturer: "Internal Design"
```

### Core Evaluation Models

#### EvaluationSession
Central container for a complete bit evaluation.

```python
EvaluationSession:
  # Core Relationships
  - serial_unit → Inventory.SerialUnit      # Physical bit
  - mat_revision → Inventory.BitDesignRevision  # MAT reference
  - job_card → Production.JobCard (optional)
  - batch_order → Production.BatchOrder (optional)

  # Context
  - context: NEW_BIT | AFTER_RUN | REPAIR_INTAKE | POST_REPAIR | RECLAIM_ONLY | RETROFIT_INTENT
  - customer_name: String
  - project_name: String

  # Workflow Status
  - status: DRAFT | UNDER_REVIEW | APPROVED | LOCKED
  - submitted_at, approved_at, locked_at: DateTime

  # Personnel
  - evaluator → HR.HREmployee (who performed evaluation)
  - reviewing_engineer → HR.HREmployee (who reviewed)
  - approved_by, locked_by → User

  # Summary Statistics (denormalized)
  - total_cells: Integer
  - replace_count: Integer (X codes)
  - ok_count: Integer (O codes)
  - braze_count: Integer (S codes)
  - rotate_count: Integer (R codes)
  - lost_count: Integer (L codes)

  # Health Metrics
  - damage_percentage: Computed (% needing action)
  - health_score: Computed (% OK cutters)

  # State Tracking
  - is_last_known_state: Boolean

  # Notes
  - general_notes, wear_pattern_notes, damage_assessment, recommendations: Text
```

#### EvaluationCell
Individual cutter position evaluation within a session.

```python
EvaluationCell:
  # Position Identification
  - evaluation_session → EvaluationSession
  - blade_number: Integer (1-based)
  - section → BitSection
  - position_index: Integer (1-based within section)
  - is_primary: Boolean (True=primary, False=secondary cutter)

  # Cutter Information
  - cutter_item → Inventory.Item (cutter design)
  - cutter_code → CutterEvaluationCode (X/O/S/R/L)

  # Feature Flags
  - has_fin_build_up: Boolean (V code)
  - fin_number: Integer (which fin affected)
  - has_pocket_damage: Boolean (P code)
  - has_impact_arrestor_issue: Boolean (I code)
  - has_body_build_up: Boolean (B code)

  # Geometric Measurements
  - pocket_diameter: Decimal (mm)
  - pocket_depth: Decimal (mm)
  - cutter_exposure: Decimal (mm above pocket)
  - wear_flat_length: Decimal (mm)
  - back_rake_angle: Decimal (degrees)
  - side_rake_angle: Decimal (degrees)

  # Tracking
  - evaluated_at: DateTime
  - notes: Text
```

### Inspection Models

#### ThreadInspection
API thread inspection for bit connections.

```python
ThreadInspection:
  - evaluation_session → EvaluationSession

  # Thread Type
  - thread_type: API_REG | API_IF | API_FH | API_NC | HT | OTHER
  - connection_type: PIN | BOX
  - thread_size: String (e.g., "4-1/2 REG")

  # Result
  - result: OK | MINOR_DAMAGE | MAJOR_DAMAGE | REPAIRABLE | SCRAP

  # Conditions
  - thread_crest_condition, thread_root_condition, shoulder_condition: String
  - galling_observed, corrosion_observed: Boolean

  # Measurements (JSON)
  - measurements_json: Dict (pitch diameter, lead, taper, etc.)

  # Recommendations
  - repair_recommendation: Text
  - requires_recut, requires_replacement: Boolean

  # Personnel
  - inspected_by → HR.HREmployee
  - inspected_at: DateTime
```

#### NDTInspection
Non-Destructive Testing results.

```python
NDTInspection:
  - evaluation_session → EvaluationSession

  # Method and Result
  - method: LPT | MPI | UT | RT | VT | OTHER
  - result: PASS | FAIL | REPAIR_REQUIRED | MONITOR | INCONCLUSIVE

  # Findings
  - areas_inspected: Text
  - indications_description: Text
  - crack_indications, porosity_indications, inclusion_indications: Boolean
  - max_indication_size: Decimal (mm)
  - indication_count: Integer

  # Acceptance
  - acceptance_standard: String (ASME, API, company standard)
  - meets_acceptance_criteria: Boolean

  # Equipment & Certification
  - equipment_used: String
  - calibration_date: Date
  - inspector_certification: String (e.g., "Level II")

  # Personnel
  - inspector → HR.HREmployee
  - inspected_at: DateTime
  - report_number: String
```

### Technical Instruction Engine

#### TechnicalInstructionTemplate
Defines rules for automated instruction generation.

```python
TechnicalInstructionTemplate:
  # Identification
  - code: "GAUGE_REPLACE_CHECK"
  - name: "Replace all damaged cutters in Gauge section"

  # Classification
  - scope: EVALUATION_SESSION | CELL_LEVEL | THREAD_LEVEL | NDT_LEVEL
  - stage: PRE_PRODUCTION | EVALUATION | PROCESSING | FINAL_QC
  - severity: INFO | WARNING | CRITICAL

  # Condition Engine (JSON)
  - condition_json: {
      "section": "GAUGE",
      "cutter_code": "X",
      "min_count": 1
    }

  # Output
  - output_template: "{count} cutter(s) marked for replacement in gauge area."

  # Behavior
  - auto_generate: Boolean
  - requires_acknowledgment: Boolean
  - can_be_overridden: Boolean
  - override_requires_approval: Boolean
  - priority: Integer (higher = processed first)

  # Versioning
  - version: Integer
  - effective_from, effective_to: DateTime
```

#### TechnicalInstructionInstance
Runtime instance generated for a specific evaluation.

```python
TechnicalInstructionInstance:
  - evaluation_session → EvaluationSession
  - template → TechnicalInstructionTemplate

  # Resolved Content
  - resolved_text: "3 cutter(s) marked for replacement in gauge area."
  - context_data: JSON (snapshot of trigger data)

  # Status
  - status: SUGGESTED | ACCEPTED | REJECTED | OVERRIDDEN | ACKNOWLEDGED

  # Override Handling
  - override_reason: Text
  - override_by → User
  - override_approved_by → User

  # Acknowledgment
  - acknowledged_by → User
  - acknowledged_at: DateTime

  # Related Data
  - related_cells: ManyToMany → EvaluationCell
```

### Requirement Models

#### RequirementTemplate
Defines mandatory workflow requirements.

```python
RequirementTemplate:
  - code: "NDT_INSPECTION_COMPLETE"
  - name: "NDT Inspection Completed"

  # Classification
  - stage: PRE_PRODUCTION | EVALUATION | PROCESSING | FINAL_QC | SHIPPING
  - requirement_type: DOCUMENT | APPROVAL | MATERIAL | DATA | INSPECTION | CERTIFICATION

  # Enforcement
  - is_mandatory: Boolean
  - can_be_waived: Boolean
  - waiver_authority: "Production Manager"

  # Condition (optional)
  - condition_json: JSON (when requirement applies)

  # Instructions
  - satisfaction_instructions: Text
  - reference_documents: ["SOP-001", "QC-PROC-002"]
  - lead_time_hours: Integer
```

#### RequirementInstance
Runtime instance for a specific evaluation.

```python
RequirementInstance:
  - evaluation_session → EvaluationSession
  - template → RequirementTemplate

  # Status
  - status: PENDING | SATISFIED | NOT_APPLICABLE | WAIVED

  # Satisfaction
  - satisfied_by → User
  - satisfied_at: DateTime
  - evidence_refs: JSON (list of documents)

  # Waiver (if applicable)
  - waived_by → User
  - waiver_reason: Text
  - waiver_approved_by → User

  # Tracking
  - due_at: DateTime
  - notes: Text
```

### Audit Trail

#### EvaluationChangeLog
Comprehensive change tracking for all evaluation data.

```python
EvaluationChangeLog:
  # Context
  - evaluation_session → EvaluationSession
  - evaluation_cell → EvaluationCell (optional)
  - thread_inspection → ThreadInspection (optional)
  - ndt_inspection → NDTInspection (optional)

  # Who
  - changed_by → User
  - ip_address: IP
  - user_agent: String

  # What
  - change_stage: EVALUATOR | ENGINEER | ADMIN | SYSTEM
  - change_type: CREATE | UPDATE | DELETE | RESTORE | STATUS_CHANGE | APPROVAL | OVERRIDE
  - model_name: String
  - object_id: BigInteger
  - field_changed: String
  - old_value: Text
  - new_value: Text

  # Why
  - reason: Text
  - additional_context: JSON

  # When
  - changed_at: DateTime
```

## Workflow States

### Session Status Flow

```
DRAFT → UNDER_REVIEW → APPROVED → LOCKED
  ↑___________↑
  (can revert)
```

| Status | Description | Editable | Actions Available |
|--------|-------------|----------|-------------------|
| **DRAFT** | Initial state, evaluator working on assessment | Yes | Edit cells, add inspections, submit for review |
| **UNDER_REVIEW** | Submitted for engineering review | Limited | Engineer can modify, approve, or send back |
| **APPROVED** | Engineering approved, ready for production | No | Can be locked, used for work orders |
| **LOCKED** | Final state, immutable record | No | View only, full audit trail available |

### Typical Workflow

1. **Evaluator Stage (DRAFT)**
   - Create evaluation session linked to serial unit
   - Complete cutter grid assessment (assign X/O/S/R/L codes)
   - Mark feature flags (V/P/I/B)
   - Record thread inspection results
   - Complete NDT inspections
   - System generates technical instructions
   - Submit for review

2. **Engineer Review Stage (UNDER_REVIEW)**
   - Review all cutter assessments
   - Verify instruction acceptance/rejection
   - Check requirement satisfaction
   - Approve or request changes
   - Changes tracked in audit log with highlighting

3. **Production Stage (APPROVED)**
   - Evaluation used for job card creation
   - Instructions guide repair operations
   - Requirements enforced before progression

4. **Archive Stage (LOCKED)**
   - Evaluation locked for regulatory compliance
   - Full audit trail preserved
   - Used for historical analysis and reporting

## Integration Points

### Inventory Integration

```python
# EvaluationSession links to:
- SerialUnit (physical bit being evaluated)
- BitDesignRevision (MAT/design reference)
- Item (cutter designs used)

# Use cases:
serial_unit.evaluation_sessions.filter(is_last_known_state=True)  # Latest evaluation
mat_revision.evaluation_sessions.count()  # How many bits use this MAT
```

### Production Integration

```python
# EvaluationSession can link to:
- JobCard (work order for repair/manufacture)
- BatchOrder (customer order grouping)

# Production uses evaluation data for:
- Determining repair scope and materials
- Generating work instructions
- Tracking cutter replacement counts
```

### HR Integration

```python
# Personnel tracking:
- evaluator → HREmployee (who performed evaluation)
- reviewing_engineer → HREmployee (who reviewed)
- inspected_by → HREmployee (inspection personnel)
- inspector → HREmployee (NDT inspector with certification)

# Enables:
- Workload tracking
- Certification verification
- Performance metrics
```

## Installation & Setup

### 1. Apply Migrations

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows

# Generate migrations
python manage.py makemigrations evaluation

# Apply migrations
python manage.py migrate evaluation
```

### 2. Load Initial Data

```bash
python manage.py loaddata floor_app/operations/evaluation/fixtures/initial_data.json
```

This loads:
- 5 cutter evaluation codes (X, O, S, R, L)
- 4 feature codes (V, P, I, B)
- 5 bit sections (CONE, NOSE, TAPER, SHOULDER, GAUGE)
- 3 bit types (HDBS, SMI_LEGACY, SMI_NEW)
- 3 technical instruction templates
- 3 requirement templates

### 3. Access the Module

Navigate to: `http://127.0.0.1:8000/evaluation/`

## URL Structure

```
/evaluation/                                    # Dashboard

# Session Management
/evaluation/sessions/                           # Session list
/evaluation/sessions/create/                    # Create new session
/evaluation/sessions/<pk>/                      # Session detail
/evaluation/sessions/<pk>/edit/                 # Edit session

# Cutter Grid
/evaluation/sessions/<pk>/grid/                 # Interactive grid editor
/evaluation/sessions/<pk>/save-cell/            # AJAX save cell data

# Inspections
/evaluation/sessions/<pk>/thread/               # Thread inspection form
/evaluation/sessions/<pk>/thread/save/          # Save thread data
/evaluation/sessions/<pk>/ndt/                  # NDT inspection form
/evaluation/sessions/<pk>/ndt/save/             # Save NDT data

# Instructions & Requirements
/evaluation/sessions/<pk>/instructions/         # View generated instructions
/evaluation/instructions/<inst_pk>/accept/      # Accept instruction
/evaluation/instructions/<inst_pk>/reject/      # Reject instruction
/evaluation/sessions/<pk>/requirements/         # View requirements
/evaluation/requirements/<req_pk>/satisfy/      # Mark requirement satisfied

# Review & Approval
/evaluation/sessions/<pk>/review/               # Engineer review interface
/evaluation/sessions/<pk>/approve/              # Approve session
/evaluation/sessions/<pk>/lock/                 # Lock session

# Output
/evaluation/sessions/<pk>/print/                # Print job card format
/evaluation/sessions/<pk>/print/summary/        # Customer-friendly summary

# History
/evaluation/sessions/<pk>/history/              # Full audit trail timeline

# Settings
/evaluation/settings/                           # Settings dashboard
/evaluation/settings/codes/                     # Cutter evaluation codes
/evaluation/settings/features/                  # Feature codes
/evaluation/settings/sections/                  # Bit sections
/evaluation/settings/types/                     # Bit types
/evaluation/settings/instruction-templates/     # Technical instruction templates
/evaluation/settings/requirement-templates/     # Requirement templates
```

## Key Features

### Interactive Cutter/Pocket Grid Editor
- Visual grid representing all blade positions
- Click-to-select evaluation codes (X/O/S/R/L)
- Real-time count updates
- Feature flag checkboxes (V/P/I/B)
- Section-aware layout (CONE→GAUGE)
- Primary/secondary cutter indication
- Notes per cell
- Geometric measurements input

### Color-Coded Evaluation Codes
- Visual distinction for quick assessment
- Red (#FF0000) for damage/replace
- Green (#00FF00) for OK status
- Orange/Yellow for repair actions
- Purple for lost cutters
- Consistent across all views

### Feature Marker Tracking
- Toggle flags for V (fin build-up), P (pocket), I (impact arrestor), B (body)
- Fin number specification for V code
- Aggregated feature counts in session summary
- Visual indicators on grid

### Thread and NDT Inspection Forms
- Comprehensive thread inspection with API standards
- Multiple NDT methods (LPT, MPI, UT, RT, VT)
- Certification tracking
- Equipment calibration records
- Pass/Fail/Monitor results
- Recommendation generation

### Technical Instruction Rule Engine
- Condition-based automatic instruction generation
- Template variables with runtime resolution
- Priority-based processing
- Severity classification (INFO/WARNING/CRITICAL)
- Accept/Reject/Override workflow
- Acknowledgment requirements
- Version control with effective dates

### Requirement Tracking and Satisfaction
- Mandatory vs optional requirements
- Waiver workflow with authority checks
- Evidence documentation
- Due date tracking
- Stage-based requirements
- Blocking enforcement

### Engineer Review with Change Highlighting
- Side-by-side comparison views
- Change highlighting in audit trail
- Override documentation
- Approval workflow
- Revert capability for non-locked sessions

### Print-Ready Job Card Output
- Formatted evaluation summary
- Cutter replacement lists
- Inspection results
- Technical instructions
- Requirement status
- Signature blocks

### Customer-Friendly Summary Views
- Executive summary of bit health
- Damage percentage visualization
- Recommendation highlights
- Cost-relevant information
- Professional formatting

### Full Audit Trail
- Every change tracked with timestamp
- User identification with IP address
- Before/after value comparison
- Reason documentation
- Stage-based categorization
- Compliance-ready reporting

## Technical Instruction Engine

### How condition_json Works

The condition engine evaluates JSON rules against evaluation data:

```json
{
  "section": "GAUGE",        // Filter by bit section
  "cutter_code": "X",        // Filter by evaluation code
  "min_count": 1             // Minimum occurrences to trigger
}
```

**Available Condition Keys:**

| Key | Type | Description |
|-----|------|-------------|
| `section` | String | BitSection code (CONE/NOSE/TAPER/SHOULDER/GAUGE) |
| `cutter_code` | String | CutterEvaluationCode (X/O/S/R/L) |
| `min_count` | Integer | Minimum number of matches |
| `max_count` | Integer | Maximum number of matches |
| `damage_percentage_min` | Float | Minimum damage percentage (0-100) |
| `damage_percentage_max` | Float | Maximum damage percentage |
| `has_features` | Boolean | True if any feature flags set |
| `ndt_result` | String | NDT inspection result |
| `thread_result` | String | Thread inspection result |

### Template Variables

Output templates support placeholder substitution:

```python
output_template = "{count} cutter(s) marked for replacement in {section} section."

# Resolved with:
context_data = {
  "count": 3,
  "section": "GAUGE",
  "damage_percentage": 45.5,
  "section_counts": {"CONE": 1, "GAUGE": 3},
  "evaluator": "John Doe"
}

# Result:
"3 cutter(s) marked for replacement in GAUGE section."
```

**Available Template Variables:**

| Variable | Description |
|----------|-------------|
| `{count}` | Number of matching cells/conditions |
| `{section}` | Section name where condition occurred |
| `{damage_percentage}` | Overall bit damage percentage |
| `{health_score}` | Bit health score (% OK) |
| `{replace_count}` | Total X codes |
| `{lost_count}` | Total L codes |
| `{evaluator}` | Evaluator name |
| `{serial_number}` | Bit serial number |
| `{mat_number}` | MAT/design number |

### Example Templates

**Critical Lost Cutter Alert:**
```json
{
  "code": "LOST_CUTTER_CRITICAL",
  "severity": "CRITICAL",
  "condition_json": {
    "cutter_code": "L",
    "min_count": 1
  },
  "output_template": "CRITICAL: {count} cutter(s) missing from bit. Investigate cause before replacement.",
  "requires_acknowledgment": true,
  "can_be_overridden": false
}
```

**High Damage Warning:**
```json
{
  "code": "HIGH_DAMAGE_ALERT",
  "severity": "WARNING",
  "condition_json": {
    "damage_percentage_min": 50
  },
  "output_template": "High damage detected: {damage_percentage}% of cutters require action.",
  "can_be_overridden": true
}
```

## Files Structure

```
floor_app/operations/evaluation/
├── __init__.py
├── apps.py
├── admin.py                          # Django admin configuration
├── urls.py                           # URL routing
├── views.py                          # View functions and classes
├── forms.py                          # Form definitions
├── models/
│   ├── __init__.py                   # Model exports
│   ├── reference.py                  # CutterEvaluationCode, FeatureCode, BitSection, BitType
│   ├── session.py                    # EvaluationSession
│   ├── cell.py                       # EvaluationCell
│   ├── inspection.py                 # ThreadInspection, NDTInspection
│   ├── instructions.py               # TechnicalInstructionTemplate, RequirementTemplate
│   ├── instances.py                  # TechnicalInstructionInstance, RequirementInstance
│   └── audit.py                      # EvaluationChangeLog
├── fixtures/
│   └── initial_data.json             # Seed data for codes, sections, templates
├── migrations/
│   └── __init__.py
├── templates/evaluation/
│   ├── dashboard.html                # Main dashboard
│   ├── sessions/
│   │   ├── list.html                 # Session list view
│   │   ├── detail.html               # Session detail view
│   │   └── form.html                 # Create/edit session form
│   ├── grid/
│   │   └── editor.html               # Interactive cutter grid
│   ├── thread/
│   │   └── form.html                 # Thread inspection form
│   ├── ndt/
│   │   └── form.html                 # NDT inspection form
│   ├── instructions/
│   │   └── list.html                 # Technical instructions list
│   ├── requirements/
│   │   └── list.html                 # Requirements tracking
│   ├── review/
│   │   └── engineer.html             # Engineer review interface
│   ├── print/
│   │   ├── job_card.html             # Print-ready job card
│   │   └── summary.html              # Customer summary
│   ├── history/
│   │   └── timeline.html             # Audit trail timeline
│   └── settings/
│       ├── dashboard.html            # Settings overview
│       ├── codes_list.html           # Evaluation codes management
│       ├── features_list.html        # Feature codes management
│       ├── sections_list.html        # Bit sections management
│       └── types_list.html           # Bit types management
└── README.md                         # This file
```

## Testing Checklist

- [ ] **Setup**
  - [ ] Run migrations successfully
  - [ ] Load initial data without errors
  - [ ] Access dashboard at /evaluation/

- [ ] **Reference Data**
  - [ ] View all cutter evaluation codes (X/O/S/R/L)
  - [ ] View all feature codes (V/P/I/B)
  - [ ] View all bit sections (CONE→GAUGE)
  - [ ] View bit types (HDBS, SMI)

- [ ] **Session Creation**
  - [ ] Create new evaluation session
  - [ ] Link to serial unit and MAT revision
  - [ ] Set context (REPAIR_INTAKE, etc.)
  - [ ] Assign evaluator

- [ ] **Grid Editor**
  - [ ] Load interactive grid for session
  - [ ] Click cells to assign codes (X/O/S/R/L)
  - [ ] Set feature flags (V/P/I/B)
  - [ ] Enter geometric measurements
  - [ ] Save changes via AJAX
  - [ ] Verify color coding displays correctly

- [ ] **Inspections**
  - [ ] Create thread inspection
  - [ ] Select thread type and connection
  - [ ] Record inspection result
  - [ ] Create NDT inspection (LPT/MPI)
  - [ ] Record indications and recommendations

- [ ] **Technical Instructions**
  - [ ] Verify auto-generated instructions appear
  - [ ] Accept instruction
  - [ ] Reject instruction with reason
  - [ ] Override instruction (if permitted)
  - [ ] Acknowledge critical instructions

- [ ] **Requirements**
  - [ ] View pending requirements
  - [ ] Satisfy mandatory requirement
  - [ ] Waive waivable requirement (with authority)
  - [ ] Verify blocking requirements prevent progression

- [ ] **Workflow**
  - [ ] Submit session for review (DRAFT → UNDER_REVIEW)
  - [ ] Engineer review changes highlighted
  - [ ] Approve session (UNDER_REVIEW → APPROVED)
  - [ ] Lock session (APPROVED → LOCKED)
  - [ ] Verify locked session is read-only

- [ ] **Output**
  - [ ] Print job card view renders correctly
  - [ ] Print summary shows customer-friendly data
  - [ ] Summary statistics match cell counts

- [ ] **Audit Trail**
  - [ ] View session history timeline
  - [ ] Verify all changes logged
  - [ ] Check user attribution
  - [ ] Validate before/after values
  - [ ] Review change reasons

- [ ] **Summary Statistics**
  - [ ] Total cells count accurate
  - [ ] Replace count (X codes) correct
  - [ ] OK count (O codes) correct
  - [ ] Damage percentage calculation
  - [ ] Health score calculation

## Future Enhancements

1. **QR Code Integration**
   - Generate QR codes linking to evaluation sessions
   - Quick mobile access for shop floor personnel
   - Scan-to-view evaluation history

2. **PDF Export**
   - Generate PDF reports matching company templates
   - Include signatures and certifications
   - Regulatory compliance formatting
   - Batch PDF generation for orders

3. **Inventory Consumption Integration**
   - Auto-deduct replacement cutters from inventory
   - Reserve materials based on evaluation
   - Track actual vs estimated material usage
   - Bill of materials generation

4. **AI-Assisted Evaluation**
   - Image recognition for cutter condition
   - Wear pattern analysis
   - Predictive maintenance recommendations
   - Automated code suggestions

5. **Advanced Reporting**
   - Customer-specific report templates
   - Trend analysis across evaluations
   - Comparative bit performance metrics
   - Cost analysis per repair type

6. **3D Visualization**
   - Interactive 3D bit model
   - Cutter position visualization
   - Wear pattern heatmaps
   - AR overlay for field evaluation

7. **Workflow Automation**
   - Automatic job card creation from evaluation
   - Email notifications for approvals
   - Slack/Teams integration
   - API for external systems

8. **Mobile Application**
   - Offline evaluation capability
   - Photo attachment per cell
   - Voice-to-text notes
   - GPS location tracking for field evaluations

---

**Module Version:** 1.0.0
**Django Compatibility:** 5.2+
**Author:** Claude Code (Anthropic)
**Last Updated:** November 2025

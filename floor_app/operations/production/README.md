# Production & Evaluation Module

A comprehensive production management system for PDC bit manufacturing and repair operations.

## Overview

This module provides:
- **Batch Order Management** - Track groups of bits under customer orders
- **Job Card System** - Per-bit work tracking and lifecycle management
- **Production Routing** - Operation sequences with time tracking
- **Cutter Evaluation** - Interactive grid-based cutter condition assessment
- **NDT & Thread Inspection** - Non-destructive testing and API thread inspection
- **Checklists & Approvals** - Workflow control and quality gates

## Architecture

### Data Model Layers

```
1. Batch Order Layer
   └─ BatchOrder (groups multiple job cards under one customer order)

2. Job Card Layer
   └─ JobCard (per-bit work tracking, links to SerialUnit, MAT)

3. Routing Layer
   ├─ JobRoute (route header per job card)
   └─ JobRouteStep (individual operations with time tracking)

4. Evaluation Layer
   ├─ CutterLayout (grid structure per MAT)
   ├─ CutterLocation (individual grid positions)
   ├─ JobCutterEvaluationHeader (evaluation session)
   ├─ JobCutterEvaluationDetail (per-cutter symbols)
   └─ JobCutterEvaluationOverride (engineer overrides)

5. Inspection Layer
   ├─ ApiThreadInspection (thread condition and repair)
   └─ NdtReport (LPT, MPI, Die Check results)

6. Checklist Layer
   ├─ JobChecklistInstance (runtime checklist per job)
   └─ JobChecklistItem (individual checklist items)

Reference Tables:
- OperationDefinition (master list of production operations)
- CutterSymbol (X, O, S, R, L, V, P, I meanings and actions)
- ChecklistTemplate (reusable checklist templates)
- ChecklistItemTemplate (template items)
```

## Key Features

### Job Card Workflow

```
NEW
  → EVALUATION_IN_PROGRESS (start evaluation)
  → AWAITING_APPROVAL (complete evaluation)
  → RELEASED_TO_SHOP (release to production)
  → IN_PRODUCTION (start production)
  → UNDER_QC (quality control)
  → COMPLETE (finish job)
```

### Cutter Symbols

| Symbol | Name | Action | Description |
|--------|------|--------|-------------|
| X | Damaged | REPLACE | Cutter must be replaced |
| O | OK | KEEP | Good condition, keep as-is |
| S | Braze Build-up | REPAIR_BRAZE | Spin cutter and add braze |
| R | Rotate | ROTATE | Rotate to expose new edge |
| L | Lost | CLEAN | Lost cutter, clean pocket |
| V | Fins | BUILD_UP | Build-up fins/blades |
| P | Pocket | BUILD_UP | Repair cutter pocket |
| I | Impact | INSPECT | Impact arrestor needs attention |

### Time Tracking

- Each route step tracks:
  - `actual_start_at` - When step started
  - `actual_end_at` - When step completed
  - `total_pause_minutes` - Accumulated pause time
  - `actual_duration_hours` - Computed net duration
  - `wait_time_from_previous` - Time between steps (KPI metric)

## Integration with Existing Modules

### Inventory Integration

```python
# Job Card links to:
- SerialUnit (physical bit)
- BitDesignRevision (initial and current MAT)
- BOMHeader (bill of materials)

# Future: InventoryTransaction
# - Job cards will link to stock movements
# - Material consumption tracking
```

### HR Integration

```python
# Route steps link to:
- HREmployee (operator, supervisor)

# Evaluations link to:
- HREmployee (evaluator, reviewer)

# Checklists link to:
- HREmployee (who completed items)
```

## Installation & Setup

### 1. Apply Migrations

```bash
# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Generate migrations
python manage.py makemigrations production

# Apply migrations
python manage.py migrate production
```

### 2. Load Initial Data

```bash
python manage.py loaddata floor_app/operations/production/fixtures/initial_data.json
```

This loads:
- 9 default operation definitions (Evaluation, De-Braze, Grinding, Brazing, Machining, NDT, Thread Inspection, Final QC, Packing)
- 8 cutter symbols (X, O, S, R, L, V, P, I)
- 2 checklist templates with sample items

### 3. Access the Module

Navigate to: `http://127.0.0.1:8000/production/`

## URL Structure

```
/production/                              # Dashboard
/production/batches/                      # Batch list
/production/batches/create/               # Create batch
/production/batches/<pk>/                 # Batch detail
/production/batches/<pk>/edit/            # Edit batch

/production/jobcards/                     # Job card list
/production/jobcards/create/              # Create job card
/production/jobcards/<pk>/                # Job card detail
/production/jobcards/<pk>/edit/           # Edit job card
/production/jobcards/<pk>/route/          # Route editor
/production/jobcards/<pk>/evaluation/     # Evaluation list

/production/settings/                     # Settings dashboard
/production/settings/operations/          # Operation definitions
/production/settings/symbols/             # Cutter symbols
/production/settings/checklist-templates/ # Checklist templates
```

## User Interface

### Dashboard Features
- Summary statistics (open batches, job cards, evaluation status)
- High priority jobs list
- Overdue jobs alert
- Active operations in progress
- Recent job cards

### Job Card Features
- Tabbed interface (Overview, Routing, Evaluations, Inspections, Checklists)
- Status-aware action buttons
- MAT revision tracking
- Customer and location info

### Cutter Evaluation Grid
- Interactive 10x20 grid (configurable)
- Click to select symbol for each cell
- Real-time count updates
- Color-coded symbols
- Submit/Approve workflow

### Routing Editor
- Add/remove/reorder operations
- Start/Complete/Skip steps
- Time tracking with pause support
- Operator assignment
- Progress visualization

## Excel Job Card Mapping

Old Excel sheets are mapped to new system:

| Excel Sheet | New Module Component |
|-------------|---------------------|
| Data (Header) | JobCard model fields |
| ARDT Cutter Entry | JobCutterEvaluationDetail with symbols |
| Eng. Cutter Entry | JobCutterEvaluationOverride |
| Instructions | ChecklistTemplate + business logic |
| API Thread Inspection | ApiThreadInspection model |
| Die Check / LPT | NdtReport model |
| E Checklist | JobChecklistInstance |
| Router Sheet | JobRoute + JobRouteStep |

## Business Logic Highlights

### Batch Completion Tracking

```python
# BatchOrder automatically updates completion when job cards complete
batch.update_completion_status()
# Calculates: completed_quantity, status (PARTIAL_COMPLETE, COMPLETE)
```

### Job Card MAT Changes

```python
# Track MAT changes (retrofit, substitution)
job_card.change_mat(new_mat, reason='Cutter shortage', user=request.user)
# Also updates SerialUnit's current_mat with history
```

### Checklist Auto-Creation

```python
# Checklists auto-create when job card is created
for template in ChecklistTemplate.objects.filter(auto_create_on_job=True):
    JobChecklistInstance.create_from_template(job_card, template)
```

### Evaluation Summary

```python
# Calculate cutter counts from symbols
evaluation.calculate_summary()
# Updates: total_cutters, replace_count, repair_count, ok_count, etc.
```

## Future Enhancements

1. **QR Code Integration** - Central QR service for job cards and bits
2. **Inventory Consumption** - Auto-deduct materials per route step
3. **PDF Export** - Generate printable job cards matching Excel format
4. **Quotation Module** - Calculate repair costs based on evaluation
5. **KPI Dashboard** - Operation time analytics, bottleneck identification
6. **Mobile Interface** - Shop floor data entry on tablets
7. **Barcode/RFID** - Scan bits to pull up job cards

## Testing Checklist

- [ ] Create a batch order
- [ ] Create a job card linked to a serial unit
- [ ] Add route steps to job card
- [ ] Start/complete route steps (verify time tracking)
- [ ] Create cutter evaluation with grid
- [ ] Enter symbols on grid
- [ ] Submit and approve evaluation
- [ ] Create NDT report
- [ ] Create thread inspection
- [ ] Complete checklist items
- [ ] Verify batch completion updates

## Files Structure

```
floor_app/operations/production/
├── __init__.py
├── apps.py
├── admin.py
├── urls.py
├── views.py
├── forms.py
├── models/
│   ├── __init__.py
│   ├── reference.py        # OperationDefinition, CutterSymbol, ChecklistTemplate
│   ├── batch.py            # BatchOrder
│   ├── job_card.py         # JobCard
│   ├── routing.py          # JobRoute, JobRouteStep
│   ├── evaluation.py       # CutterLayout, Evaluation models
│   ├── inspection.py       # ApiThreadInspection, NdtReport
│   └── checklist.py        # JobChecklistInstance, JobChecklistItem
├── fixtures/
│   └── initial_data.json   # Seed data
├── migrations/
│   └── __init__.py
├── templates/production/
│   ├── dashboard.html
│   ├── batches/
│   ├── jobcards/
│   ├── routing/
│   ├── evaluation/
│   ├── ndt/
│   ├── thread_inspection/
│   ├── checklists/
│   └── settings/
└── README.md               # This file
```

## Support

For issues or questions, check:
- Admin panel: `/admin/production/`
- Django logs for errors
- Model docstrings for field descriptions

---

**Module Version:** 1.0.0
**Django Compatibility:** 5.2+
**Author:** Claude Code (Anthropic)
**Last Updated:** November 2025

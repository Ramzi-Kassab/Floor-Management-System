# Feature-Level Routing Map: NDT, Evaluations, Thread Inspections, Checklists

**Analysis Date:** 2025-11-21
**Branch:** analysis/routing-and-templates-xray

---

## 1. NDT Inspections

### Production App - NDT Reports

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| NDT Inspections | production | `floor_app.operations.production.views.ndt_list` (function) | `jobcards/<int:pk>/ndt/` | `production:ndt_list` | `production/ndt/list.html` | `NdtReport` |
| NDT Inspections | production | `floor_app.operations.production.views.NdtCreateView` (class) | `jobcards/<int:pk>/ndt/create/` | `production:ndt_create` | `production/ndt/form.html` | `NdtReport` |
| NDT Inspections | production | `floor_app.operations.production.views.ndt_detail` (function) | `ndt/<int:ndt_pk>/` | `production:ndt_detail` | `production/ndt/detail.html` | `NdtReport` |
| NDT Inspections | production | `floor_app.operations.production.views.NdtUpdateView` (class) | `ndt/<int:ndt_pk>/edit/` | `production:ndt_edit` | `production/ndt/form.html` | `NdtReport` |
| **NDT Inspections (Global)** | **production** | **`floor_app.operations.production.views.NdtListAllView` (class)** | **`ndt-reports/`** | **`production:ndt_list_all`** | **`production/ndt/list.html`** | **`NdtReport`** |

**View Details:**
- **Jobcard-scoped views** (`ndt_list`, `ndt_create`): Require a `pk` parameter (jobcard ID), show/create NDT reports for a specific job card
- **Global view** (`NdtListAllView`): Shows ALL NDT reports across all job cards, used by Production Dashboard
- **Model Location:** `floor_app.operations.production.models.inspection.NdtReport`

**Template Locations:**
```
floor_app/operations/production/templates/production/ndt/
├── list.html      (used by both ndt_list and NdtListAllView)
├── form.html      (used by create and edit)
└── detail.html
```

### Evaluation App - NDT Inspection (Different Feature)

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| NDT Inspection (within Evaluation Session) | evaluation | `floor_app.operations.evaluation.views.ndt_inspection` (function) | `sessions/<int:pk>/ndt/` | `evaluation:ndt_inspection` | `evaluation/ndt/form.html` | Unknown (likely session-related) |
| NDT Inspection (within Evaluation Session) | evaluation | `floor_app.operations.evaluation.views.save_ndt_inspection` (function) | `sessions/<int:pk>/ndt/save/` | `evaluation:save_ndt_inspection` | N/A (AJAX endpoint) | Unknown |

**Important Note:** The `evaluation` app has its own NDT-related views, but these appear to be part of the "Evaluation Session" workflow, NOT the same as Production's NDT Reports. These are **separate, unrelated features** with similar names.

---

## 2. Evaluations

### Production App - Cutter Evaluations

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_list` (function) | `jobcards/<int:pk>/evaluation/` | `production:evaluation_list` | `production/evaluation/list.html` | `JobCutterEvaluationHeader` |
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_create` (function) | `jobcards/<int:pk>/evaluation/create/` | `production:evaluation_create` | `production/evaluation/create.html` | `JobCutterEvaluationHeader`, `JobCutterEvaluationDetail` |
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_detail` (function) | `evaluations/<int:eval_pk>/` | `production:evaluation_detail` | `production/evaluation/detail.html` | `JobCutterEvaluationHeader`, `JobCutterEvaluationDetail` |
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_edit` (function) | `evaluations/<int:eval_pk>/edit/` | `production:evaluation_edit` | `production/evaluation/edit.html` | `JobCutterEvaluationHeader`, `JobCutterEvaluationDetail` |
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_submit` (function) | `evaluations/<int:eval_pk>/submit/` | `production:evaluation_submit` | N/A (redirect) | `JobCutterEvaluationHeader` |
| Cutter Evaluations | production | `floor_app.operations.production.views.evaluation_approve` (function) | `evaluations/<int:eval_pk>/approve/` | `production:evaluation_approve` | N/A (redirect) | `JobCutterEvaluationHeader` |
| **Cutter Evaluations (Global)** | **production** | **`floor_app.operations.production.views.EvaluationListAllView` (class)** | **`evaluations/`** | **`production:evaluation_list_all`** | **`production/evaluation/list.html`** | **`JobCutterEvaluationHeader`** |

**View Details:**
- **Jobcard-scoped views** (`evaluation_list`, `evaluation_create`): Require a `pk` parameter (jobcard ID)
- **Global view** (`EvaluationListAllView`): Shows ALL evaluations across all job cards, used by Production Dashboard
- **Models Location:**
  - `floor_app.operations.production.models.evaluation.JobCutterEvaluationHeader`
  - `floor_app.operations.production.models.evaluation.JobCutterEvaluationDetail`

**Template Locations:**
```
floor_app/operations/production/templates/production/evaluation/
├── list.html      (used by both evaluation_list and EvaluationListAllView)
├── create.html
├── detail.html
└── edit.html
```

### Evaluation App - Evaluation Sessions (Different Feature)

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.dashboard` (function) | `` (empty, root) | `evaluation:dashboard` | `evaluation/dashboard.html` | Various |
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.EvaluationSessionListView` (class) | `sessions/` | `evaluation:session_list` | `evaluation/sessions/list.html` | Unknown (Session model) |
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.EvaluationSessionCreateView` (class) | `sessions/create/` | `evaluation:session_create` | `evaluation/sessions/form.html` | Unknown |
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.EvaluationSessionDetailView` (class) | `sessions/<int:pk>/` | `evaluation:session_detail` | `evaluation/sessions/detail.html` | Unknown |
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.EvaluationSessionUpdateView` (class) | `sessions/<int:pk>/edit/` | `evaluation:session_edit` | `evaluation/sessions/form.html` | Unknown |
| Evaluation Sessions | evaluation | `floor_app.operations.evaluation.views.grid_editor` (function) | `sessions/<int:pk>/grid/` | `evaluation:grid_editor` | `evaluation/grid/editor.html` | Unknown |

**Template Locations:**
```
floor_app/operations/evaluation/templates/evaluation/
├── dashboard.html
├── sessions/
│   ├── list.html
│   ├── form.html
│   └── detail.html
├── grid/
│   └── editor.html
├── thread/
│   └── form.html
├── ndt/
│   └── form.html
└── ... (many more)
```

**Important Note:** The `evaluation` app manages "Evaluation Sessions" which is a **completely different feature** from Production's "Cutter Evaluations". These are two separate evaluation systems:
1. **Production Cutter Evaluations**: Evaluating cutters/bits during production
2. **Evaluation Sessions**: A separate evaluation workflow system (purpose unclear from code alone)

---

## 3. Thread Inspections

### Production App - API Thread Inspections

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| Thread Inspections | production | `floor_app.operations.production.views.thread_inspection_list` (function) | `jobcards/<int:pk>/thread-inspection/` | `production:thread_inspection_list` | `production/thread_inspection/list.html` | `ApiThreadInspection` |
| Thread Inspections | production | `floor_app.operations.production.views.ThreadInspectionCreateView` (class) | `jobcards/<int:pk>/thread-inspection/create/` | `production:thread_inspection_create` | `production/thread_inspection/form.html` | `ApiThreadInspection` |
| Thread Inspections | production | `floor_app.operations.production.views.thread_inspection_detail` (function) | `thread-inspections/<int:insp_pk>/` | `production:thread_inspection_detail` | `production/thread_inspection/detail.html` | `ApiThreadInspection` |
| Thread Inspections | production | `floor_app.operations.production.views.ThreadInspectionUpdateView` (class) | `thread-inspections/<int:insp_pk>/edit/` | `production:thread_inspection_edit` | `production/thread_inspection/form.html` | `ApiThreadInspection` |
| Thread Inspections | production | `floor_app.operations.production.views.thread_inspection_complete_repair` (function) | `thread-inspections/<int:insp_pk>/complete-repair/` | `production:thread_inspection_complete_repair` | N/A (redirect) | `ApiThreadInspection` |
| **Thread Inspections (Global)** | **production** | **`floor_app.operations.production.views.ThreadInspectionListAllView` (class)** | **`thread-inspections/`** | **`production:thread_inspection_list_all`** | **`production/thread_inspection/list.html`** | **`ApiThreadInspection`** |

**View Details:**
- **Jobcard-scoped views**: Require a `pk` parameter (jobcard ID)
- **Global view** (`ThreadInspectionListAllView`): Shows ALL thread inspections across all job cards
- **Model Location:** `floor_app.operations.production.models.inspection.ApiThreadInspection`

**Template Locations:**
```
floor_app/operations/production/templates/production/thread_inspection/
├── list.html      (used by both thread_inspection_list and ThreadInspectionListAllView)
├── form.html
└── detail.html
```

### Evaluation App - Thread Inspection (Different Feature)

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| Thread Inspection (within Evaluation Session) | evaluation | `floor_app.operations.evaluation.views.thread_inspection` (function) | `sessions/<int:pk>/thread/` | `evaluation:thread_inspection` | `evaluation/thread/form.html` | Unknown |
| Thread Inspection (within Evaluation Session) | evaluation | `floor_app.operations.evaluation.views.save_thread_inspection` (function) | `sessions/<int:pk>/thread/save/` | `evaluation:save_thread_inspection` | N/A (AJAX endpoint) | Unknown |

**Important Note:** Similar to NDT, the `evaluation` app has thread inspection views that are part of the Evaluation Session workflow, NOT the same as Production's API Thread Inspections.

---

## 4. Production/Quality Checklists

### Production App - Job Checklists

| Feature | App Name | View Name (with module path) | URL Pattern | URL Name | Template Name | Related Model(s) |
|---------|----------|-------------------------------|-------------|----------|---------------|------------------|
| Checklists | production | `floor_app.operations.production.views.checklist_list` (function) | `jobcards/<int:pk>/checklists/` | `production:checklist_list` | `production/checklists/list.html` | `JobChecklistInstance`, `JobChecklistItem` |
| Checklists | production | `floor_app.operations.production.views.checklist_detail` (function) | `checklists/<int:checklist_pk>/` | `production:checklist_detail` | `production/checklists/detail.html` | `JobChecklistInstance`, `JobChecklistItem` |
| Checklists | production | `floor_app.operations.production.views.checklist_item_complete` (function) | `checklist-items/<int:item_pk>/complete/` | `production:checklist_item_complete` | N/A (redirect) | `JobChecklistItem` |
| Checklist Templates | production | `floor_app.operations.production.views.ChecklistTemplateListView` (class) | `settings/checklist-templates/` | `production:checklist_template_list` | `production/settings/checklist_template_list.html` | `ChecklistTemplate` |
| **Checklists (Global)** | **production** | **`floor_app.operations.production.views.ChecklistListAllView` (class)** | **`checklists-all/`** | **`production:checklist_list_all`** | **`production/checklists/list.html`** | **`JobChecklistInstance`** |

**View Details:**
- **Jobcard-scoped views**: Require a `pk` parameter (jobcard ID)
- **Global view** (`ChecklistListAllView`): Shows ALL checklists across all job cards
- **Models Location:**
  - `floor_app.operations.production.models.checklist.JobChecklistInstance`
  - `floor_app.operations.production.models.checklist.JobChecklistItem`
  - `floor_app.operations.production.models.reference.ChecklistTemplate`

**Template Locations:**
```
floor_app/operations/production/templates/production/checklists/
├── list.html      (used by both checklist_list and ChecklistListAllView)
└── detail.html

floor_app/operations/production/templates/production/settings/
└── checklist_template_list.html
```

### Quality App - NO Checklist Views Found

**Analysis Result:** The `quality` app (`floor_app/operations/quality/urls.py`) does NOT contain any checklist-related views. Quality management uses:
- NCR (Non-Conformance Reports)
- Calibration management
- Dispositions
- Acceptance criteria

But NO checklist functionality. Checklists are owned exclusively by the `production` app.

---

## Summary Table: Feature Ownership

| Feature | Owned By App | Has Jobcard-Scoped Views? | Has Global List View? | Used on Production Dashboard? |
|---------|--------------|---------------------------|-----------------------|-------------------------------|
| **Cutter Evaluations** | `production` | ✅ Yes (6 views) | ✅ Yes (`evaluation_list_all`) | ✅ Yes |
| **NDT Reports** | `production` | ✅ Yes (4 views) | ✅ Yes (`ndt_list_all`) | ✅ Yes |
| **API Thread Inspections** | `production` | ✅ Yes (5 views) | ✅ Yes (`thread_inspection_list_all`) | ✅ Yes |
| **Job Checklists** | `production` | ✅ Yes (3 views + templates) | ✅ Yes (`checklist_list_all`) | ✅ Yes |
| Evaluation Sessions | `evaluation` | ✅ Yes (10+ views) | ✅ Yes (`session_list`) | ❌ No (has own dashboard) |
| Session NDT/Thread | `evaluation` | ✅ Yes (4 views) | ❌ No | ❌ No (part of session workflow) |

---

## Key Findings

### ✅ All Features Have Dedicated Views

**Good news:** ALL four features (NDT, Evaluations, Thread Inspections, Checklists) have their own dedicated views and URL patterns. None are reusing JobCard routes.

### ✅ Global vs Jobcard-Scoped Views

Each feature has TWO types of views:

1. **Jobcard-scoped views** (older, require `pk` parameter):
   - Used within a specific jobcard's detail page
   - URL pattern includes `jobcards/<int:pk>/...`
   - Example: `/production/jobcards/123/ndt/`

2. **Global list views** (recently added):
   - Show all records across ALL jobcards
   - Used by Production Dashboard cards
   - URL pattern does NOT include jobcard ID
   - Example: `/production/ndt-reports/`

### ⚠️ Naming Confusion: Two "Evaluation" Systems

The project has TWO separate evaluation systems:

1. **Production App - Cutter Evaluations**
   - Purpose: Evaluate cutters/bits during production
   - Models: `JobCutterEvaluationHeader`, `JobCutterEvaluationDetail`
   - URLs: `production:evaluation_*`

2. **Evaluation App - Evaluation Sessions**
   - Purpose: Unknown (separate evaluation workflow system)
   - Models: Unknown (Session-related)
   - URLs: `evaluation:session_*`
   - Has its own NDT and Thread inspection sub-features

**This is NOT a bug**, but it can be confusing for developers/users. The naming suggests these should be the same feature, but they're architecturally separate.

### ⚠️ Template Reuse Pattern

Several views share templates (e.g., `production/ndt/list.html` is used by both `ndt_list` and `NdtListAllView`). This is intentional and works correctly because the global views set `job_card=None` in context to signal "global mode" to the template.

### ❌ No Quality App Involvement

Despite the title "Quality Features", the `quality` app does NOT own NDT, Thread Inspections, or Checklists. These are all owned by the `production` app. The quality app focuses on:
- Non-conformance reports (NCRs)
- Calibration management
- Quality dispositions

This may or may not align with the intended architecture.

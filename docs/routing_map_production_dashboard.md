# Production Dashboard Routing Map

**Analysis Date:** 2025-11-21
**Branch:** analysis/routing-and-templates-xray
**Dashboard URL:** `/production/`

---

## Template Structure

### Main Dashboard Template
- **Path:** `floor_app/operations/production/templates/production/dashboard.html`
- **Extends:** `base.html`
- **View Function:** `floor_app.operations.production.views.dashboard`
- **URL Pattern:** `path('', views.dashboard, name='dashboard')`
- **URL Name:** `production:dashboard`

### Base Template (Inherited)
- **Path:** `floor_app/templates/base.html`
- **Contains:** Global navigation sidebar with collapsible department sections

---

## Dashboard Card/Link Inventory

### Header Action Buttons

| Section / Label | Template File | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| "New Batch" | `production/dashboard.html:18` | `<a>` | `production:batch_create` | `floor_app.operations.production.views.BatchCreateView` | `path('batches/create/', ...)` | ✅ Correct |
| "New Job Card" | `production/dashboard.html:21` | `<a>` | `production:jobcard_create` | `floor_app.operations.production.views.JobCardCreateView` | `path('jobcards/create/', ...)` | ✅ Correct |

### Quick Access Cards (Main Content)

| Section / Label | Template File | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| "View Batches" | `production/dashboard.html:115` | `<a>` | `production:batch_list` | `floor_app.operations.production.views.BatchListView` | `path('batches/', ...)` | ✅ Correct |
| "View Job Cards" | `production/dashboard.html:133` | `<a>` | `production:jobcard_list` | `floor_app.operations.production.views.JobCardListView` | `path('jobcards/', ...)` | ✅ Correct |
| "View Evaluations" | `production/dashboard.html:151` | `<a>` | `production:evaluation_list_all` | `floor_app.operations.production.views.EvaluationListAllView` | `path('evaluations/', ...)` | ✅ New global view (recently added) |
| "View NDT Records" | `production/dashboard.html:169` | `<a>` | `production:ndt_list_all` | `floor_app.operations.production.views.NdtListAllView` | `path('ndt-reports/', ...)` | ✅ New global view (recently added) |
| "View Thread Inspections" | `production/dashboard.html:187` | `<a>` | `production:thread_inspection_list_all` | `floor_app.operations.production.views.ThreadInspectionListAllView` | `path('thread-inspections/', ...)` | ✅ New global view (recently added) |
| "View Checklists" | `production/dashboard.html:205` | `<a>` | `production:checklist_list_all` | `floor_app.operations.production.views.ChecklistListAllView` | `path('checklists-all/', ...)` | ✅ New global view (recently added) |

### Active Jobs Sidebar

| Section / Label | Template File | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| Job card detail link | `production/dashboard.html:227` | `<a>` | `production:jobcard_detail` | `floor_app.operations.production.views.JobCardDetailView` | `path('jobcards/<int:pk>/', ...)` | ✅ Correct |

### Quick Actions (Right Sidebar)

| Section / Label | Template File | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| "New Batch" | `production/dashboard.html:276` | `<a>` | `production:batch_create` | `floor_app.operations.production.views.BatchCreateView` | `path('batches/create/', ...)` | ✅ Correct |
| "New Job Card" | `production/dashboard.html:279` | `<a>` | `production:jobcard_create` | `floor_app.operations.production.views.JobCardCreateView` | `path('jobcards/create/', ...)` | ✅ Correct |
| "Settings" | `production/dashboard.html:283` | `<a>` | `production:settings` | `floor_app.operations.production.views.settings_dashboard` | `path('settings/', ...)` | ✅ Correct |

---

## Base Template Sidebar - Production Section

**Template:** `floor_app/templates/base.html`

| Section / Label | Template Line | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| "Production Dashboard" | `base.html:405` | `<a>` | `production:dashboard` | `floor_app.operations.production.views.dashboard` | `path('', ...)` | ✅ Correct |
| "Batch Orders" | `base.html:411` | `<a>` | `production:batch_list` | `floor_app.operations.production.views.BatchListView` | `path('batches/', ...)` | ✅ Correct |
| "Job Cards" | `base.html:417` | `<a>` | `production:jobcard_list` | `floor_app.operations.production.views.JobCardListView` | `path('jobcards/', ...)` | ✅ Correct |
| "Settings" | `base.html:423` | `<a>` | `production:settings` | `floor_app.operations.production.views.settings_dashboard` | `path('settings/', ...)` | ✅ Correct |

**Note:** The Production sidebar section does NOT include direct links to NDT, Thread Inspections, or Checklists. These are accessible via the dashboard cards only.

---

## Base Template Sidebar - Evaluation Section

**Template:** `floor_app/templates/base.html`

| Section / Label | Template Line | HTML Element | URL Name Used | View Function/Class | URL Pattern | Notes |
|-----------------|---------------|--------------|---------------|---------------------|-------------|-------|
| "Evaluation Dashboard" | `base.html:440` | `<a>` | `evaluation:dashboard` | `floor_app.operations.evaluation.views.dashboard` | `path('', ...)` | ✅ Correct - Different app (evaluation) |
| "Evaluation Sessions" | `base.html:446` | `<a>` | `evaluation:session_list` | `floor_app.operations.evaluation.views.EvaluationSessionListView` | `path('sessions/', ...)` | ⚠️ This is for "Evaluation Sessions" (different from Production Evaluations/Cutter Evaluations) |
| "Settings" | `base.html:452` | `<a>` | `evaluation:settings_dashboard` | `floor_app.operations.evaluation.views.settings_dashboard` | `path('settings/', ...)` | ✅ Correct |

**Important Note:** The `evaluation` app handles "Evaluation Sessions" which appear to be a different feature than the "Cutter Evaluations" shown on the Production Dashboard. These are separate systems:
- **Production Evaluations** (Cutter Evaluations): Managed by `production` app, model `JobCutterEvaluationHeader`
- **Evaluation Sessions**: Managed by `evaluation` app, likely for different evaluation workflows

---

## Analysis Summary

### ✅ No Incorrect Routing Found

All dashboard cards on the Production Dashboard (`/production/`) are currently pointing to **correct, dedicated views**:

1. **Job Cards** → `production:jobcard_list` ✅
2. **Batches** → `production:batch_list` ✅
3. **Evaluations** → `production:evaluation_list_all` ✅ (recently added)
4. **NDT Inspections** → `production:ndt_list_all` ✅ (recently added)
5. **Thread Inspections** → `production:thread_inspection_list_all` ✅ (recently added)
6. **Checklists** → `production:checklist_list_all` ✅ (recently added)

### Recent Changes

Based on the URL patterns and view code, it appears that four new **global list views** were recently added to the production app:
- `EvaluationListAllView` (lines 850-875 in views.py)
- `NdtListAllView` (lines 878-907 in views.py)
- `ThreadInspectionListAllView` (lines 910-939 in views.py)
- `ChecklistListAllView` (lines 942-968 in views.py)

These views provide **cross-jobcard** lists (showing all records across all job cards), whereas the older views were **jobcard-scoped**:
- `evaluation_list(request, pk)` - Shows evaluations for a specific job card
- `ndt_list(request, pk)` - Shows NDT reports for a specific job card
- `thread_inspection_list(request, pk)` - Shows thread inspections for a specific job card
- `checklist_list(request, pk)` - Shows checklists for a specific job card

### Architecture Observation

The system has TWO separate evaluation systems:
1. **Production Cutter Evaluations** (`production` app) - Used for evaluating cutters/bits in production
2. **Evaluation Sessions** (`evaluation` app) - A separate evaluation workflow system

This is **not a routing error**, but an intentional separation of concerns.

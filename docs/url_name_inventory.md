# Project-Wide URL Name Inventory

**Analysis Date:** 2025-11-21
**Branch:** analysis/routing-and-templates-xray

---

## Summary of Potential Conflicts

### ⚠️ Duplicate URL Names Found

| URL Name | Apps Using It | Conflict Level | Notes |
|----------|---------------|----------------|-------|
| `settings_dashboard` | `evaluation`, `inventory`, `quality` | ⚠️ Medium | Multiple apps use the same name for their settings page |
| `features_list` | `evaluation` | ⚠️ Low | Alias for `feature_list` in same app |
| `serial_unit_create` | `inventory` | ⚠️ Low | Alias for `serialunit_create` in same app |

### ✅ No Conflicts Found For

The following features do NOT have URL name conflicts:
- **NDT-related URLs**: All owned by `production` app
- **Thread Inspection URLs**: All owned by `production` app
- **Checklist URLs**: All owned by `production` app
- **Cutter Evaluation URLs**: All owned by `production` app
- **JobCard URLs**: All owned by `production` app

---

## URL Inventory by App

### 1. Production App (`production`)

**App Name:** `production`
**URL Prefix:** `/production/`

| URL Name | URL Pattern | View Function/Class | Template Name |
|----------|-------------|---------------------|---------------|
| `dashboard` | `` (empty) | `floor_app.operations.production.views.dashboard` | `production/dashboard.html` |
| **Batch Orders** ||||
| `batch_list` | `batches/` | `floor_app.operations.production.views.BatchListView` | `production/batches/list.html` |
| `batch_create` | `batches/create/` | `floor_app.operations.production.views.BatchCreateView` | `production/batches/form.html` |
| `batch_detail` | `batches/<int:pk>/` | `floor_app.operations.production.views.BatchDetailView` | `production/batches/detail.html` |
| `batch_edit` | `batches/<int:pk>/edit/` | `floor_app.operations.production.views.BatchUpdateView` | `production/batches/form.html` |
| **Job Cards** ||||
| `jobcard_list` | `jobcards/` | `floor_app.operations.production.views.JobCardListView` | `production/jobcards/list.html` |
| `jobcard_create` | `jobcards/create/` | `floor_app.operations.production.views.JobCardCreateView` | `production/jobcards/form.html` |
| `jobcard_detail` | `jobcards/<int:pk>/` | `floor_app.operations.production.views.JobCardDetailView` | `production/jobcards/detail.html` |
| `jobcard_edit` | `jobcards/<int:pk>/edit/` | `floor_app.operations.production.views.JobCardUpdateView` | `production/jobcards/form.html` |
| `jobcard_start_evaluation` | `jobcards/<int:pk>/start-evaluation/` | `floor_app.operations.production.views.jobcard_start_evaluation` | N/A (redirect) |
| `jobcard_complete_evaluation` | `jobcards/<int:pk>/complete-evaluation/` | `floor_app.operations.production.views.jobcard_complete_evaluation` | N/A (redirect) |
| `jobcard_release` | `jobcards/<int:pk>/release/` | `floor_app.operations.production.views.jobcard_release` | N/A (redirect) |
| `jobcard_start_production` | `jobcards/<int:pk>/start-production/` | `floor_app.operations.production.views.jobcard_start_production` | N/A (redirect) |
| `jobcard_complete` | `jobcards/<int:pk>/complete/` | `floor_app.operations.production.views.jobcard_complete` | N/A (redirect) |
| **Routing** ||||
| `route_editor` | `jobcards/<int:pk>/route/` | `floor_app.operations.production.views.route_editor` | `production/routing/editor.html` |
| `route_add_step` | `jobcards/<int:pk>/route/add-step/` | `floor_app.operations.production.views.route_add_step` | `production/routing/add_step.html` |
| `route_step_start` | `route-steps/<int:step_pk>/start/` | `floor_app.operations.production.views.route_step_start` | N/A (redirect) |
| `route_step_complete` | `route-steps/<int:step_pk>/complete/` | `floor_app.operations.production.views.route_step_complete` | `production/routing/complete_step.html` |
| `route_step_skip` | `route-steps/<int:step_pk>/skip/` | `floor_app.operations.production.views.route_step_skip` | N/A (redirect) |
| **Cutter Evaluation (Jobcard-Scoped)** ||||
| `evaluation_list` | `jobcards/<int:pk>/evaluation/` | `floor_app.operations.production.views.evaluation_list` | `production/evaluation/list.html` |
| `evaluation_create` | `jobcards/<int:pk>/evaluation/create/` | `floor_app.operations.production.views.evaluation_create` | `production/evaluation/create.html` |
| `evaluation_detail` | `evaluations/<int:eval_pk>/` | `floor_app.operations.production.views.evaluation_detail` | `production/evaluation/detail.html` |
| `evaluation_edit` | `evaluations/<int:eval_pk>/edit/` | `floor_app.operations.production.views.evaluation_edit` | `production/evaluation/edit.html` |
| `evaluation_submit` | `evaluations/<int:eval_pk>/submit/` | `floor_app.operations.production.views.evaluation_submit` | N/A (redirect) |
| `evaluation_approve` | `evaluations/<int:eval_pk>/approve/` | `floor_app.operations.production.views.evaluation_approve` | N/A (redirect) |
| **NDT & Thread Inspection (Jobcard-Scoped)** ||||
| `ndt_list` | `jobcards/<int:pk>/ndt/` | `floor_app.operations.production.views.ndt_list` | `production/ndt/list.html` |
| `ndt_create` | `jobcards/<int:pk>/ndt/create/` | `floor_app.operations.production.views.NdtCreateView` | `production/ndt/form.html` |
| `ndt_detail` | `ndt/<int:ndt_pk>/` | `floor_app.operations.production.views.ndt_detail` | `production/ndt/detail.html` |
| `ndt_edit` | `ndt/<int:ndt_pk>/edit/` | `floor_app.operations.production.views.NdtUpdateView` | `production/ndt/form.html` |
| `thread_inspection_list` | `jobcards/<int:pk>/thread-inspection/` | `floor_app.operations.production.views.thread_inspection_list` | `production/thread_inspection/list.html` |
| `thread_inspection_create` | `jobcards/<int:pk>/thread-inspection/create/` | `floor_app.operations.production.views.ThreadInspectionCreateView` | `production/thread_inspection/form.html` |
| `thread_inspection_detail` | `thread-inspections/<int:insp_pk>/` | `floor_app.operations.production.views.thread_inspection_detail` | `production/thread_inspection/detail.html` |
| `thread_inspection_edit` | `thread-inspections/<int:insp_pk>/edit/` | `floor_app.operations.production.views.ThreadInspectionUpdateView` | `production/thread_inspection/form.html` |
| `thread_inspection_complete_repair` | `thread-inspections/<int:insp_pk>/complete-repair/` | `floor_app.operations.production.views.thread_inspection_complete_repair` | N/A (redirect) |
| **Checklists (Jobcard-Scoped)** ||||
| `checklist_list` | `jobcards/<int:pk>/checklists/` | `floor_app.operations.production.views.checklist_list` | `production/checklists/list.html` |
| `checklist_detail` | `checklists/<int:checklist_pk>/` | `floor_app.operations.production.views.checklist_detail` | `production/checklists/detail.html` |
| `checklist_item_complete` | `checklist-items/<int:item_pk>/complete/` | `floor_app.operations.production.views.checklist_item_complete` | N/A (redirect) |
| **Settings** ||||
| `settings` | `settings/` | `floor_app.operations.production.views.settings_dashboard` | `production/settings/dashboard.html` |
| `operation_list` | `settings/operations/` | `floor_app.operations.production.views.OperationListView` | `production/settings/operation_list.html` |
| `symbol_list` | `settings/symbols/` | `floor_app.operations.production.views.SymbolListView` | `production/settings/symbol_list.html` |
| `checklist_template_list` | `settings/checklist-templates/` | `floor_app.operations.production.views.ChecklistTemplateListView` | `production/settings/checklist_template_list.html` |
| **Global List Views (Dashboard Cards)** ||||
| `evaluation_list_all` | `evaluations/` | `floor_app.operations.production.views.EvaluationListAllView` | `production/evaluation/list.html` |
| `ndt_list_all` | `ndt-reports/` | `floor_app.operations.production.views.NdtListAllView` | `production/ndt/list.html` |
| `thread_inspection_list_all` | `thread-inspections/` | `floor_app.operations.production.views.ThreadInspectionListAllView` | `production/thread_inspection/list.html` |
| `checklist_list_all` | `checklists-all/` | `floor_app.operations.production.views.ChecklistListAllView` | `production/checklists/list.html` |

**Total URLs:** 47

---

### 2. Evaluation App (`evaluation`)

**App Name:** `evaluation`
**URL Prefix:** `/evaluation/`

| URL Name | URL Pattern | View Function/Class | Template Name |
|----------|-------------|---------------------|---------------|
| `dashboard` | `` (empty) | `floor_app.operations.evaluation.views.dashboard` | `evaluation/dashboard.html` |
| **Evaluation Sessions** ||||
| `session_list` | `sessions/` | `floor_app.operations.evaluation.views.EvaluationSessionListView` | `evaluation/sessions/list.html` |
| `session_create` | `sessions/create/` | `floor_app.operations.evaluation.views.EvaluationSessionCreateView` | `evaluation/sessions/form.html` |
| `session_detail` | `sessions/<int:pk>/` | `floor_app.operations.evaluation.views.EvaluationSessionDetailView` | `evaluation/sessions/detail.html` |
| `session_edit` | `sessions/<int:pk>/edit/` | `floor_app.operations.evaluation.views.EvaluationSessionUpdateView` | `evaluation/sessions/form.html` |
| **Cell Grid Editor** ||||
| `grid_editor` | `sessions/<int:pk>/grid/` | `floor_app.operations.evaluation.views.grid_editor` | `evaluation/grid/editor.html` |
| `save_cell` | `sessions/<int:pk>/save-cell/` | `floor_app.operations.evaluation.views.save_cell` | N/A (AJAX) |
| **Thread Inspection (Session-Scoped)** ||||
| `thread_inspection` | `sessions/<int:pk>/thread/` | `floor_app.operations.evaluation.views.thread_inspection` | `evaluation/thread/form.html` |
| `save_thread_inspection` | `sessions/<int:pk>/thread/save/` | `floor_app.operations.evaluation.views.save_thread_inspection` | N/A (AJAX) |
| **NDT Inspection (Session-Scoped)** ||||
| `ndt_inspection` | `sessions/<int:pk>/ndt/` | `floor_app.operations.evaluation.views.ndt_inspection` | `evaluation/ndt/form.html` |
| `save_ndt_inspection` | `sessions/<int:pk>/ndt/save/` | `floor_app.operations.evaluation.views.save_ndt_inspection` | N/A (AJAX) |
| **Technical Instructions** ||||
| `instructions_list` | `sessions/<int:pk>/instructions/` | `floor_app.operations.evaluation.views.instructions_list` | `evaluation/instructions/list.html` |
| `accept_instruction` | `instructions/<int:inst_pk>/accept/` | `floor_app.operations.evaluation.views.accept_instruction` | N/A (redirect) |
| `reject_instruction` | `instructions/<int:inst_pk>/reject/` | `floor_app.operations.evaluation.views.reject_instruction` | N/A (redirect) |
| **Requirements** ||||
| `requirements_list` | `sessions/<int:pk>/requirements/` | `floor_app.operations.evaluation.views.requirements_list` | `evaluation/requirements/list.html` |
| `satisfy_requirement` | `requirements/<int:req_pk>/satisfy/` | `floor_app.operations.evaluation.views.satisfy_requirement` | N/A (redirect) |
| **Engineer Review** ||||
| `engineer_review` | `sessions/<int:pk>/review/` | `floor_app.operations.evaluation.views.engineer_review` | `evaluation/review/engineer.html` |
| `approve_session` | `sessions/<int:pk>/approve/` | `floor_app.operations.evaluation.views.approve_session` | N/A (redirect) |
| `lock_session` | `sessions/<int:pk>/lock/` | `floor_app.operations.evaluation.views.lock_session` | N/A (redirect) |
| **Print Views** ||||
| `print_job_card` | `sessions/<int:pk>/print/` | `floor_app.operations.evaluation.views.print_job_card` | `evaluation/print/job_card.html` |
| `print_summary` | `sessions/<int:pk>/print/summary/` | `floor_app.operations.evaluation.views.print_summary` | `evaluation/print/summary.html` |
| **History** ||||
| `history_view` | `sessions/<int:pk>/history/` | `floor_app.operations.evaluation.views.history_view` | `evaluation/history/timeline.html` |
| **Settings** ||||
| `settings_dashboard` | `settings/` | `floor_app.operations.evaluation.views.settings_dashboard` | `evaluation/settings/dashboard.html` |
| `code_list` | `settings/codes/` | `floor_app.operations.evaluation.views.CodeListView` | `evaluation/settings/codes_list.html` |
| `feature_list` | `settings/features/` | `floor_app.operations.evaluation.views.FeatureListView` | `evaluation/settings/features_list.html` |
| `features_list` | `settings/features/` | `floor_app.operations.evaluation.views.FeatureListView` | `evaluation/settings/features_list.html` |
| `section_list` | `settings/sections/` | `floor_app.operations.evaluation.views.SectionListView` | `evaluation/settings/sections_list.html` |
| `type_list` | `settings/types/` | `floor_app.operations.evaluation.views.TypeListView` | `evaluation/settings/types_list.html` |
| `instruction_template_list` | `settings/instruction-templates/` | `floor_app.operations.evaluation.views.InstructionTemplateListView` | Unknown |
| `requirement_template_list` | `settings/requirement-templates/` | `floor_app.operations.evaluation.views.RequirementTemplateListView` | Unknown |

**Total URLs:** 29
**Note:** `features_list` is an alias for `feature_list` (duplicate URL name in same app)

---

### 3. Quality App (`quality`)

**App Name:** `quality`
**URL Prefix:** `/quality/`

| URL Name | URL Pattern | View Function/Class | Template Name |
|----------|-------------|---------------------|---------------|
| `dashboard` | `` (empty) | `floor_app.operations.quality.views.dashboard` | `quality/dashboard.html` |
| **NCR Management** ||||
| `ncr_list` | `ncrs/` | `floor_app.operations.quality.views.ncr_list` | `quality/ncr/list.html` |
| `ncr_create` | `ncrs/create/` | `floor_app.operations.quality.views.ncr_create` | `quality/ncr/form.html` |
| `ncr_detail` | `ncrs/<int:pk>/` | `floor_app.operations.quality.views.ncr_detail` | `quality/ncr/detail.html` |
| `ncr_edit` | `ncrs/<int:pk>/edit/` | `floor_app.operations.quality.views.ncr_edit` | `quality/ncr/form.html` |
| `ncr_add_analysis` | `ncrs/<int:pk>/add-analysis/` | `floor_app.operations.quality.views.ncr_add_analysis` | `quality/ncr/add_analysis.html` |
| `ncr_add_action` | `ncrs/<int:pk>/add-action/` | `floor_app.operations.quality.views.ncr_add_action` | `quality/ncr/add_action.html` |
| `ncr_close` | `ncrs/<int:pk>/close/` | `floor_app.operations.quality.views.ncr_close` | `quality/ncr/close_confirm.html` |
| **Calibration Management** ||||
| `calibration_list` | `calibration/` | `floor_app.operations.quality.views.calibration_list` | `quality/calibration/overview.html` |
| `equipment_list` | `calibration/equipment/` | `floor_app.operations.quality.views.equipment_list` | `quality/calibration/equipment_list.html` |
| `equipment_create` | `calibration/equipment/create/` | `floor_app.operations.quality.views.equipment_create` | `quality/calibration/equipment_form.html` |
| `equipment_detail` | `calibration/equipment/<int:pk>/` | `floor_app.operations.quality.views.equipment_detail` | `quality/calibration/equipment_detail.html` |
| `equipment_edit` | `calibration/equipment/<int:pk>/edit/` | `floor_app.operations.quality.views.equipment_edit` | `quality/calibration/equipment_form.html` |
| `record_calibration` | `calibration/equipment/<int:pk>/record/` | `floor_app.operations.quality.views.record_calibration` | `quality/calibration/record_form.html` |
| `calibration_due` | `calibration/due/` | `floor_app.operations.quality.views.calibration_due` | `quality/calibration/due_list.html` |
| `calibration_overdue` | `calibration/overdue/` | `floor_app.operations.quality.views.calibration_overdue` | `quality/calibration/due_list.html` |
| **Quality Disposition** ||||
| `disposition_list` | `dispositions/` | `floor_app.operations.quality.views.disposition_list` | `quality/disposition/list.html` |
| `disposition_create` | `dispositions/create/` | `floor_app.operations.quality.views.disposition_create` | `quality/disposition/form.html` |
| `disposition_detail` | `dispositions/<int:pk>/` | `floor_app.operations.quality.views.disposition_detail` | `quality/disposition/detail.html` |
| `disposition_release` | `dispositions/<int:pk>/release/` | `floor_app.operations.quality.views.disposition_release` | `quality/disposition/release_confirm.html` |
| `generate_coc` | `dispositions/<int:pk>/generate-coc/` | `floor_app.operations.quality.views.generate_coc` | `quality/disposition/generate_coc_confirm.html` |
| **Acceptance Criteria** ||||
| `criteria_list` | `criteria/` | `floor_app.operations.quality.views.criteria_list` | `quality/acceptance/list.html` |
| `criteria_detail` | `criteria/<int:pk>/` | `floor_app.operations.quality.views.criteria_detail` | `quality/acceptance/detail.html` |
| **Reports** ||||
| `reports_dashboard` | `reports/` | `floor_app.operations.quality.views.reports_dashboard` | `quality/reports/dashboard.html` |
| `ncr_summary_report` | `reports/ncr-summary/` | `floor_app.operations.quality.views.ncr_summary_report` | `quality/reports/ncr_summary.html` |
| `calibration_status_report` | `reports/calibration-status/` | `floor_app.operations.quality.views.calibration_status_report` | `quality/reports/calibration_status.html` |
| **Settings** ||||
| `settings_dashboard` | `settings/` | `floor_app.operations.quality.views.settings_dashboard` | `quality/settings/dashboard.html` |

**Total URLs:** 27

**Important Note:** The Quality app does NOT contain any NDT, Thread Inspection, or Checklist functionality. It focuses on:
- Non-Conformance Reports (NCRs)
- Calibration management
- Quality dispositions
- Acceptance criteria

---

### 4. Inventory App (`inventory`)

**App Name:** `inventory`
**URL Prefix:** `/inventory/`

| URL Name | URL Pattern | View Function/Class | Template Name |
|----------|-------------|---------------------|---------------|
| `dashboard` | `` (empty) | `floor_app.operations.inventory.views.dashboard` | `inventory/dashboard.html` |
| **Items** ||||
| `item_list` | `items/` | `floor_app.operations.inventory.views.ItemListView` | `inventory/items/list.html` |
| `item_create` | `items/create/` | `floor_app.operations.inventory.views.ItemCreateView` | `inventory/items/form.html` |
| `item_detail` | `items/<int:pk>/` | `floor_app.operations.inventory.views.ItemDetailView` | `inventory/items/detail.html` |
| `item_edit` | `items/<int:pk>/edit/` | `floor_app.operations.inventory.views.ItemUpdateView` | `inventory/items/form.html` |
| **Bit Designs** ||||
| `bitdesign_list` | `bit-designs/` | `floor_app.operations.inventory.views.BitDesignListView` | `inventory/bit_designs/list.html` |
| `bitdesign_create` | `bit-designs/create/` | `floor_app.operations.inventory.views.BitDesignCreateView` | `inventory/bit_designs/form.html` |
| `bitdesign_detail` | `bit-designs/<int:pk>/` | `floor_app.operations.inventory.views.BitDesignDetailView` | `inventory/bit_designs/detail.html` |
| `bitdesign_edit` | `bit-designs/<int:pk>/edit/` | `floor_app.operations.inventory.views.BitDesignUpdateView` | `inventory/bit_designs/form.html` |
| **MATs (Bit Design Revisions)** ||||
| `mat_list` | `mats/` | `floor_app.operations.inventory.views.BitDesignRevisionListView` | Unknown |
| `mat_create` | `mats/create/` | `floor_app.operations.inventory.views.BitDesignRevisionCreateView` | Unknown |
| `mat_detail` | `mats/<int:pk>/` | `floor_app.operations.inventory.views.BitDesignRevisionDetailView` | Unknown |
| `mat_edit` | `mats/<int:pk>/edit/` | `floor_app.operations.inventory.views.BitDesignRevisionUpdateView` | Unknown |
| **Locations** ||||
| `location_list` | `locations/` | `floor_app.operations.inventory.views.LocationListView` | `inventory/settings/location_list.html` |
| `location_create` | `locations/create/` | `floor_app.operations.inventory.views.LocationCreateView` | Unknown |
| `location_detail` | `locations/<int:pk>/` | `floor_app.operations.inventory.views.LocationDetailView` | Unknown |
| `location_edit` | `locations/<int:pk>/edit/` | `floor_app.operations.inventory.views.LocationUpdateView` | Unknown |
| **Serial Units** ||||
| `serialunit_list` | `serial-units/` | `floor_app.operations.inventory.views.SerialUnitListView` | `inventory/serial_units/list.html` |
| `serialunit_create` | `serial-units/create/` | `floor_app.operations.inventory.views.SerialUnitCreateView` | `inventory/serial_units/form.html` |
| `serial_unit_create` | `serial-units/create/` | `floor_app.operations.inventory.views.SerialUnitCreateView` | `inventory/serial_units/form.html` |
| `serialunit_detail` | `serial-units/<int:pk>/` | `floor_app.operations.inventory.views.SerialUnitDetailView` | `inventory/serial_units/detail.html` |
| `serialunit_edit` | `serial-units/<int:pk>/edit/` | `floor_app.operations.inventory.views.SerialUnitUpdateView` | `inventory/serial_units/form.html` |
| **Stock** ||||
| `stock_list` | `stock/` | `floor_app.operations.inventory.views.InventoryStockListView` | `inventory/stock/list.html` |
| `stock_detail` | `stock/<int:pk>/` | `floor_app.operations.inventory.views.InventoryStockDetailView` | `inventory/stock/detail.html` |
| `stock_adjust` | `stock/adjust/` | `floor_app.operations.inventory.views.stock_adjustment` | Unknown |
| `stock_adjustment_create` | `stock/adjust/create/` | `floor_app.operations.inventory.views.stock_adjustment` | Unknown |
| **BOMs** ||||
| `bom_list` | `boms/` | `floor_app.operations.inventory.views.BOMListView` | `inventory/boms/list.html` |
| `bom_create` | `boms/create/` | `floor_app.operations.inventory.views.BOMCreateView` | `inventory/boms/form.html` |
| `bom_detail` | `boms/<int:pk>/` | `floor_app.operations.inventory.views.BOMDetailView` | `inventory/boms/detail.html` |
| `bom_edit` | `boms/<int:pk>/edit/` | `floor_app.operations.inventory.views.BOMUpdateView` | `inventory/boms/form.html` |
| **Transactions** ||||
| `transaction_list` | `transactions/` | `floor_app.operations.inventory.views.TransactionListView` | `inventory/transactions/list.html` |
| `transaction_detail` | `transactions/<int:pk>/` | `floor_app.operations.inventory.views.TransactionDetailView` | `inventory/transactions/detail.html` |
| `transaction_create` | `transactions/create/` | `floor_app.operations.inventory.views.transaction_create` | Unknown |
| **Settings** ||||
| `settings` | `settings/` | `floor_app.operations.inventory.views.settings_dashboard` | `inventory/settings/dashboard.html` |
| `settings_dashboard` | `settings/` | `floor_app.operations.inventory.views.settings_dashboard` | `inventory/settings/dashboard.html` |
| `condition_list` | `settings/conditions/` | `floor_app.operations.inventory.views.ConditionTypeListView` | `inventory/settings/condition_list.html` |
| `ownership_list` | `settings/ownership/` | `floor_app.operations.inventory.views.OwnershipTypeListView` | `inventory/settings/ownership_list.html` |
| `category_list` | `settings/categories/` | `floor_app.operations.inventory.views.ItemCategoryListView` | `inventory/settings/category_list.html` |
| `uom_list` | `settings/uom/` | `floor_app.operations.inventory.views.UOMListView` | `inventory/settings/uom_list.html` |

**Total URLs:** 39
**Note:** `serial_unit_create` is an alias for `serialunit_create` (duplicate URL name in same app)
**Note:** `settings_dashboard` is an alias for `settings` (duplicate URL name in same app)

---

## Conflict Analysis

### settings_dashboard Conflict

**Apps Using This Name:**
- `evaluation:settings_dashboard` → `/evaluation/settings/`
- `quality:settings_dashboard` → `/quality/settings/`
- `inventory:settings_dashboard` → `/inventory/settings/`

**Risk Level:** ⚠️ Medium

**Impact:**
- When using `{% url 'settings_dashboard' %}` without app prefix, Django will use the FIRST match found based on URL include order
- Should use app-prefixed names: `{% url 'evaluation:settings_dashboard' %}`
- This is a **naming convention issue**, not a routing error, as long as views use app prefixes

**Recommendation:**
- Always use app-prefixed URL names in templates: `{% url 'app:settings_dashboard' %}`
- Or rename to be more specific: `evaluation_settings`, `quality_settings`, `inventory_settings`

---

## Summary Statistics

| App | Total URL Patterns | Duplicate Names (within app) | Conflicts (across apps) |
|-----|-------------------|------------------------------|-------------------------|
| production | 47 | 0 | 0 |
| evaluation | 29 | 1 (`features_list`) | 1 (`settings_dashboard`) |
| quality | 27 | 0 | 1 (`settings_dashboard`) |
| inventory | 39 | 2 (`serial_unit_create`, `settings_dashboard`) | 1 (`settings_dashboard`) |

**Total Project URLs (sampled apps):** 142

---

## Key Findings

### ✅ No Routing Conflicts for Key Features

The four key features analyzed (NDT, Evaluations, Thread Inspections, Checklists) do NOT have URL name conflicts:
- All production-related URLs use `production:` prefix
- All evaluation-session-related URLs use `evaluation:` prefix
- No overlap or ambiguity

### ⚠️ Settings Dashboard Naming

Multiple apps use `settings_dashboard` as a URL name. This is a common pattern but can cause confusion. Best practice is to always use app-prefixed names.

### ✅ Clear Separation

The URL namespace clearly separates:
- **Production Cutter Evaluations** (`production:evaluation_*`)
- **Evaluation Sessions** (`evaluation:session_*`)
- **Production NDT** (`production:ndt_*`)
- **Evaluation Session NDT** (`evaluation:ndt_inspection`)

This separation is intentional and architecturally sound.

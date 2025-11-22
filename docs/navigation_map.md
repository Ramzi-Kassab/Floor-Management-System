# Complete Navigation Map - Floor Management System

**Date:** 2025-11-22
**Branch:** cleanup/navigation-fix (to be created)
**Purpose:** Comprehensive URL, view, and template mapping

---

## Executive Summary

This document provides a complete mapping of all Django apps, URLs, views, and templates in the Floor Management System. Use this as the single source of truth for navigation and routing.

### Quick Stats
- **Total Apps:** 31 operational modules
- **URL Namespaces:** 31 unique namespaces
- **Major Dashboards:** 12 primary module dashboards
- **Template Directories:** 13+ app-specific locations
- **API Endpoints:** 16 separate API configurations

---

## 1. PROJECT ROOT URLs

**File:** `floor_mgmt/urls.py`
**Base URL:** `/`

### 1.1 Authentication (No Namespace)

| URL Name | Pattern | View | Template |
|----------|---------|------|----------|
| signup | `/signup/` | floor_views.signup | registration/signup.html |
| login | `/accounts/login/` | CustomLoginView | registration/login.html |
| logout | `/accounts/logout/` | CustomLogoutView | - |
| password_reset | `/accounts/password_reset/` | CustomPasswordResetView | registration/password_reset.html |
| password_reset_confirm | `/accounts/reset/<uidb64>/<token>/` | CustomPasswordResetConfirmView | registration/password_reset_confirm.html |

### 1.2 Legacy Employee Management (No Namespace)

| URL Name | Pattern | View |
|----------|---------|------|
| employee_list | `/employees/` | floor_views.employee_list |
| employee_detail | `/employees/<pk>/` | floor_views.employee_detail |

### 1.3 Module Includes (With Namespaces)

| Namespace | URL Prefix | Module Path |
|-----------|-----------|-------------|
| core | `/` | core.urls |
| hr | `/hr/` | floor_app.operations.hr.urls |
| inventory | `/inventory/` | floor_app.operations.inventory.urls |
| production | `/production/` | floor_app.operations.production.urls |
| evaluation | `/evaluation/` | floor_app.operations.evaluation.urls |
| quality | `/quality/` | floor_app.operations.quality.urls |
| qrcodes | `/qrcodes/` | floor_app.operations.qrcodes.urls |
| purchasing | `/purchasing/` | floor_app.operations.purchasing.urls |
| knowledge | `/knowledge/` | floor_app.operations.knowledge.urls |
| maintenance | `/maintenance/` | floor_app.operations.maintenance.urls |
| planning | `/planning/` | floor_app.operations.planning.urls |
| sales | `/sales/` | floor_app.operations.sales.urls |
| analytics | `/analytics/` | floor_app.operations.analytics.urls |
| notifications | `/notifications/` | floor_app.operations.notifications.urls |
| approvals | `/approvals/` | floor_app.operations.approvals.urls |
| device_tracking | `/devices/` | floor_app.operations.device_tracking.urls |
| gps_system | `/gps/` | floor_app.operations.gps_system.urls |
| qr_system | `/qr/` | floor_app.operations.qr_system.urls |
| chat | `/chat/` | floor_app.operations.chat.urls |
| data_extraction | `/data-extraction/` | floor_app.operations.data_extraction.urls |
| fives | `/fives/` | floor_app.operations.fives.urls |
| hr_assets | `/hr-assets/` | floor_app.operations.hr_assets.urls |
| hiring | `/hiring/` | floor_app.operations.hiring.urls |
| hoc | `/hoc/` | floor_app.operations.hoc.urls |
| journey_management | `/journey/` | floor_app.operations.journey_management.urls |
| meetings | `/meetings/` | floor_app.operations.meetings.urls |
| user_preferences | `/preferences/` | floor_app.operations.user_preferences.urls |
| utility_tools | `/utils/` | floor_app.operations.utility_tools.urls |
| vendor_portal | `/vendors/` | floor_app.operations.vendor_portal.urls |
| retrieval | `/retrieval/` | floor_app.operations.retrieval.urls |

---

## 2. CORE APP (Main Dashboard & System)

**Namespace:** `core`
**Base URL:** `/`
**URLs File:** `core/urls.py`
**Templates:** `core/templates/core/`

### 2.1 Main Navigation

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| home | `/` | main_dashboard | main_dashboard.html | **Main system dashboard** |
| global_search | `/search/` | global_search | - | Global search |
| finance_dashboard | `/finance/` | finance_dashboard | finance_dashboard.html | Finance dashboard |

### 2.2 User Settings

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| user_preferences | `/settings/` | user_preferences | User settings page |
| reset_table_columns | `/settings/reset-columns/` | reset_table_columns | Reset table preferences |

### 2.3 Finance & ERP

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| costcenter_list | `/cost-centers/` | CostCenterListView | Cost centers list |
| costcenter_create | `/cost-centers/create/` | CostCenterCreateView | Create cost center |
| costcenter_detail | `/cost-centers/<pk>/` | CostCenterDetailView | Cost center details |
| costcenter_edit | `/cost-centers/<pk>/edit/` | CostCenterUpdateView | Edit cost center |
| erpreference_list | `/erp-references/` | ERPReferenceListView | ERP references |
| lossofsale_list | `/loss-of-sale/` | LossOfSaleEventListView | Loss of sale events |
| lossofsale_create | `/loss-of-sale/create/` | LossOfSaleEventCreateView | Create loss event |
| lossofsale_detail | `/loss-of-sale/<pk>/` | LossOfSaleEventDetailView | Loss event details |

### 2.4 System Administration

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| user_list | `/system/users/` | UserListView | System users |
| user_create | `/system/users/create/` | UserCreateView | Create user |
| user_detail | `/system/users/<pk>/` | UserDetailView | User details |
| user_edit | `/system/users/<pk>/edit/` | UserUpdateView | Edit user |
| user_password_change | `/system/users/<pk>/password/` | user_password_change | Change user password |
| user_delete | `/system/users/<pk>/delete/` | user_delete | Delete user |
| user_toggle_active | `/system/users/<pk>/toggle-active/` | user_toggle_active | Toggle user active status |
| user_permissions | `/system/users/<pk>/permissions/` | user_permissions | Manage user permissions |
| group_list | `/system/groups/` | GroupListView | Groups list |
| group_create | `/system/groups/create/` | GroupCreateView | Create group |
| group_detail | `/system/groups/<pk>/` | GroupDetailView | Group details |
| group_edit | `/system/groups/<pk>/edit/` | GroupUpdateView | Edit group |
| group_delete | `/system/groups/<pk>/delete/` | group_delete | Delete group |
| permission_list | `/system/permissions/` | PermissionListView | Permissions list |
| contenttype_list | `/system/content-types/` | ContentTypeListView | Content types |
| adminlog_list | `/system/admin-log/` | AdminLogListView | Admin activity log |
| session_list | `/system/sessions/` | SessionListView | Active sessions |

### 2.5 Health Check APIs

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| health_check | `/api/health/` | health_check | System health check |
| readiness_check | `/api/health/ready/` | readiness_check | Readiness probe (K8s) |
| liveness_check | `/api/health/live/` | liveness_check | Liveness probe (K8s) |

### 2.6 Core APIs

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| api_table_columns | `/api/user-preferences/table-columns/` | TableColumnsAPIView | Table columns API |
| global_search_api | `/api/search/` | global_search_api | Global search API |

### 2.7 Main Dashboard Cards

**Template:** `core/templates/core/main_dashboard.html`

| Card Title | Target URL | Namespace | Description |
|-----------|-----------|-----------|-------------|
| Human Resources | {% url 'hr:dashboard' %} | hr | HR management |
| Inventory | {% url 'inventory:dashboard' %} | inventory | Materials management |
| Production | {% url 'production:dashboard' %} | production | Production management |
| Quality | {% url 'quality:dashboard' %} | quality | Quality management |
| Sales | {% url 'sales:dashboard' %} | sales | Sales & lifecycle |
| Finance | {% url 'core:finance_dashboard' %} | core | Finance dashboard |

---

## 3. PRODUCTION APP

**Namespace:** `production`
**Base URL:** `/production/`
**URLs File:** `floor_app/operations/production/urls.py`
**Templates:** `floor_app/operations/production/templates/production/`
**App Name in URLs:** `production`

### 3.1 Dashboard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| dashboard | `/production/` | dashboard | dashboard.html | **Production dashboard** |

### 3.2 Global List Views (✅ Recently Added for Dashboard Cards)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| evaluation_list_all | `/production/evaluations/` | EvaluationListAllView | evaluation/list.html | **All evaluations (global)** |
| ndt_list_all | `/production/ndt-reports/` | NdtListAllView | ndt/list.html | **All NDT reports (global)** |
| thread_inspection_list_all | `/production/thread-inspections/` | ThreadInspectionListAllView | thread_inspection/list.html | **All thread inspections (global)** |
| checklist_list_all | `/production/checklists-all/` | ChecklistListAllView | checklists/list.html | **All checklists (global)** |

### 3.3 Batch Orders

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| batch_list | `/production/batches/` | BatchListView | batches/list.html | Batches list |
| batch_create | `/production/batches/create/` | BatchCreateView | batches/form.html | Create batch |
| batch_detail | `/production/batches/<pk>/` | BatchDetailView | batches/detail.html | Batch details |
| batch_edit | `/production/batches/<pk>/edit/` | BatchUpdateView | batches/form.html | Edit batch |

### 3.4 Job Cards

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| jobcard_list | `/production/jobcards/` | JobCardListView | jobcards/list.html | Job cards list |
| jobcard_create | `/production/jobcards/create/` | JobCardCreateView | jobcards/form.html | Create job card |
| jobcard_detail | `/production/jobcards/<pk>/` | JobCardDetailView | jobcards/detail.html | Job card details |
| jobcard_edit | `/production/jobcards/<pk>/edit/` | JobCardUpdateView | jobcards/form.html | Edit job card |

### 3.5 Job Card Workflow Actions

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| jobcard_start_evaluation | `/production/jobcards/<pk>/start-evaluation/` | jobcard_start_evaluation | Start evaluation phase |
| jobcard_complete_evaluation | `/production/jobcards/<pk>/complete-evaluation/` | jobcard_complete_evaluation | Complete evaluation |
| jobcard_release | `/production/jobcards/<pk>/release/` | jobcard_release | Release to production |
| jobcard_start_production | `/production/jobcards/<pk>/start-production/` | jobcard_start_production | Start production |
| jobcard_complete | `/production/jobcards/<pk>/complete/` | jobcard_complete | Complete job card |

### 3.6 Routing & Operations

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| route_editor | `/production/jobcards/<pk>/route/` | route_editor | routing/editor.html | Route editor |
| route_add_step | `/production/jobcards/<pk>/route/add-step/` | route_add_step | routing/add_step.html | Add route step |
| route_step_start | `/production/route-steps/<step_pk>/start/` | route_step_start | - | Start route step |
| route_step_complete | `/production/route-steps/<step_pk>/complete/` | route_step_complete | routing/complete_step.html | Complete route step |
| route_step_skip | `/production/route-steps/<step_pk>/skip/` | route_step_skip | - | Skip route step |

### 3.7 Cutter Evaluations (Jobcard-Scoped)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| evaluation_list | `/production/jobcards/<pk>/evaluation/` | evaluation_list | evaluation/list.html | Evaluations for job card |
| evaluation_create | `/production/jobcards/<pk>/evaluation/create/` | evaluation_create | evaluation/create.html | Create evaluation |
| evaluation_detail | `/production/evaluations/<eval_pk>/` | evaluation_detail | evaluation/detail.html | Evaluation details |
| evaluation_edit | `/production/evaluations/<eval_pk>/edit/` | evaluation_edit | evaluation/edit.html | Edit evaluation |
| evaluation_submit | `/production/evaluations/<eval_pk>/submit/` | evaluation_submit | - | Submit evaluation |
| evaluation_approve | `/production/evaluations/<eval_pk>/approve/` | evaluation_approve | - | Approve evaluation |

### 3.8 NDT Reports (Jobcard-Scoped)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| ndt_list | `/production/jobcards/<pk>/ndt/` | ndt_list | ndt/list.html | NDT reports for job card |
| ndt_create | `/production/jobcards/<pk>/ndt/create/` | NdtCreateView | ndt/form.html | Create NDT report |
| ndt_detail | `/production/ndt/<ndt_pk>/` | ndt_detail | ndt/detail.html | NDT report details |
| ndt_edit | `/production/ndt/<ndt_pk>/edit/` | NdtUpdateView | ndt/form.html | Edit NDT report |

### 3.9 Thread Inspections (Jobcard-Scoped)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| thread_inspection_list | `/production/jobcards/<pk>/thread-inspection/` | thread_inspection_list | thread_inspection/list.html | Thread inspections for job card |
| thread_inspection_create | `/production/jobcards/<pk>/thread-inspection/create/` | ThreadInspectionCreateView | thread_inspection/form.html | Create thread inspection |
| thread_inspection_detail | `/production/thread-inspections/<insp_pk>/` | thread_inspection_detail | thread_inspection/detail.html | Thread inspection details |
| thread_inspection_edit | `/production/thread-inspections/<insp_pk>/edit/` | ThreadInspectionUpdateView | thread_inspection/form.html | Edit thread inspection |
| thread_inspection_complete_repair | `/production/thread-inspections/<insp_pk>/complete-repair/` | thread_inspection_complete_repair | - | Complete thread repair |

### 3.10 Production Checklists (Jobcard-Scoped)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| checklist_list | `/production/jobcards/<pk>/checklists/` | checklist_list | checklists/list.html | Checklists for job card |
| checklist_detail | `/production/checklists/<checklist_pk>/` | checklist_detail | checklists/detail.html | Checklist details |
| checklist_item_complete | `/production/checklist-items/<item_pk>/complete/` | checklist_item_complete | - | Complete checklist item |

### 3.11 Production Settings

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| settings | `/production/settings/` | settings_dashboard | settings/dashboard.html | Production settings |
| operation_list | `/production/settings/operations/` | OperationListView | settings/operation_list.html | Operations list |
| symbol_list | `/production/settings/symbols/` | SymbolListView | settings/symbol_list.html | Symbols list |
| checklist_template_list | `/production/settings/checklist-templates/` | ChecklistTemplateListView | settings/checklist_template_list.html | Checklist templates |

### 3.12 Production Dashboard Cards

**Template:** `floor_app/operations/production/templates/production/dashboard.html`

| Card Title | Target URL | URL Name | Type | Status |
|-----------|-----------|----------|------|--------|
| Production Batches | `/production/batches/` | production:batch_list | List | ✅ Correct |
| Job Cards | `/production/jobcards/` | production:jobcard_list | List | ✅ Correct |
| Evaluations | `/production/evaluations/` | production:evaluation_list_all | **Global List** | ✅ **Fixed** |
| NDT Inspections | `/production/ndt-reports/` | production:ndt_list_all | **Global List** | ✅ **Fixed** |
| Thread Inspections | `/production/thread-inspections/` | production:thread_inspection_list_all | **Global List** | ✅ **Fixed** |
| Checklists | `/production/checklists-all/` | production:checklist_list_all | **Global List** | ✅ **Fixed** |

**Key Fix (Phase 1.3):** All four cards now route to correct global list views instead of job cards page.

---

## 4. QUALITY APP

**Namespace:** `quality`
**Base URL:** `/quality/`
**URLs File:** `floor_app/operations/quality/urls.py`
**Templates:** `floor_app/operations/quality/templates/quality/`
**App Name in URLs:** `quality`

### 4.1 Dashboard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| dashboard | `/quality/` | dashboard | dashboard.html | **Quality dashboard** |

### 4.2 Non-Conformance Reports (NCRs)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| ncr_list | `/quality/ncrs/` | ncr_list | ncr/list.html | NCRs list |
| ncr_create | `/quality/ncrs/create/` | ncr_create | ncr/form.html | Create NCR |
| ncr_detail | `/quality/ncrs/<pk>/` | ncr_detail | ncr/detail.html | NCR details |
| ncr_edit | `/quality/ncrs/<pk>/edit/` | ncr_edit | ncr/form.html | Edit NCR |
| ncr_add_analysis | `/quality/ncrs/<pk>/add-analysis/` | ncr_add_analysis | ncr/add_analysis.html | Add root cause analysis |
| ncr_add_action | `/quality/ncrs/<pk>/add-action/` | ncr_add_action | ncr/add_action.html | Add corrective action |
| ncr_close | `/quality/ncrs/<pk>/close/` | ncr_close | ncr/close_confirm.html | Close NCR |

### 4.3 Calibration Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| calibration_list | `/quality/calibration/` | calibration_list | calibration/overview.html | Calibration overview |
| equipment_list | `/quality/calibration/equipment/` | equipment_list | calibration/equipment_list.html | Equipment list |
| equipment_create | `/quality/calibration/equipment/create/` | equipment_create | calibration/equipment_form.html | Create equipment |
| equipment_detail | `/quality/calibration/equipment/<pk>/` | equipment_detail | calibration/equipment_detail.html | Equipment details |
| equipment_edit | `/quality/calibration/equipment/<pk>/edit/` | equipment_edit | calibration/equipment_form.html | Edit equipment |
| record_calibration | `/quality/calibration/equipment/<pk>/record/` | record_calibration | calibration/record_form.html | Record calibration |
| calibration_due | `/quality/calibration/due/` | calibration_due | calibration/due_list.html | Calibration due soon |
| calibration_overdue | `/quality/calibration/overdue/` | calibration_overdue | calibration/due_list.html | Overdue calibration |

### 4.4 Quality Dispositions

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| disposition_list | `/quality/dispositions/` | disposition_list | disposition/list.html | Dispositions list |
| disposition_create | `/quality/dispositions/create/` | disposition_create | disposition/form.html | Create disposition |
| disposition_detail | `/quality/dispositions/<pk>/` | disposition_detail | disposition/detail.html | Disposition details |
| disposition_release | `/quality/dispositions/<pk>/release/` | disposition_release | disposition/release_confirm.html | Release disposition |
| generate_coc | `/quality/dispositions/<pk>/generate-coc/` | generate_coc | disposition/generate_coc_confirm.html | Generate Certificate of Conformance |

### 4.5 Acceptance Criteria

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| criteria_list | `/quality/criteria/` | criteria_list | acceptance/list.html | Acceptance criteria |
| criteria_detail | `/quality/criteria/<pk>/` | criteria_detail | acceptance/detail.html | Criteria details |

### 4.6 Quality Reports

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| reports_dashboard | `/quality/reports/` | reports_dashboard | reports/dashboard.html | Reports dashboard |
| ncr_summary_report | `/quality/reports/ncr-summary/` | ncr_summary_report | reports/ncr_summary.html | NCR summary report |
| calibration_status_report | `/quality/reports/calibration-status/` | calibration_status_report | reports/calibration_status.html | Calibration status |

### 4.7 Quality Settings

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| settings | `/quality/settings/` | settings_dashboard | settings/dashboard.html | Quality settings |

### 4.8 Quality Dashboard Quick Actions

**Template:** `floor_app/operations/quality/templates/quality/dashboard.html`

| Card Title | Target URL | URL Name | Description |
|-----------|-----------|----------|-------------|
| All NCRs | `/quality/ncrs/` | quality:ncr_list | View all NCRs |
| Calibration Overview | `/quality/calibration/` | quality:calibration_list | Calibration dashboard |
| Quality Dispositions | `/quality/dispositions/` | quality:disposition_list | View dispositions |
| Reports | `/quality/reports/` | quality:reports_dashboard | Quality reports |

---

## 5. EVALUATION APP (Evaluation Sessions)

**Namespace:** `evaluation`
**Base URL:** `/evaluation/`
**URLs File:** `floor_app/operations/evaluation/urls.py`
**Templates:** `floor_app/operations/evaluation/templates/evaluation/`
**App Name in URLs:** `evaluation`

**⚠️ Note:** This is a SEPARATE evaluation system from Production Cutter Evaluations. This handles Evaluation Sessions with grid editing, technical instructions, and requirements.

### 5.1 Dashboard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| dashboard | `/evaluation/` | dashboard | dashboard.html | **Evaluation dashboard** |

### 5.2 Evaluation Sessions

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| session_list | `/evaluation/sessions/` | EvaluationSessionListView | sessions/list.html | Sessions list |
| session_create | `/evaluation/sessions/create/` | EvaluationSessionCreateView | sessions/form.html | Create session |
| session_detail | `/evaluation/sessions/<pk>/` | EvaluationSessionDetailView | sessions/detail.html | Session details |
| session_edit | `/evaluation/sessions/<pk>/edit/` | EvaluationSessionUpdateView | sessions/form.html | Edit session |

### 5.3 Grid Editor

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| grid_editor | `/evaluation/sessions/<pk>/grid/` | grid_editor | grid/editor.html | Grid editor |
| save_cell | `/evaluation/sessions/<pk>/save-cell/` | save_cell | - | Save cell data (AJAX) |

### 5.4 Session Thread & NDT (⚠️ Different from Production)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| thread_inspection | `/evaluation/sessions/<pk>/thread/` | thread_inspection | thread/form.html | Session thread inspection |
| save_thread_inspection | `/evaluation/sessions/<pk>/thread/save/` | save_thread_inspection | - | Save thread data (AJAX) |
| ndt_inspection | `/evaluation/sessions/<pk>/ndt/` | ndt_inspection | ndt/form.html | Session NDT inspection |
| save_ndt_inspection | `/evaluation/sessions/<pk>/ndt/save/` | save_ndt_inspection | - | Save NDT data (AJAX) |

### 5.5 Technical Instructions

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| instructions_list | `/evaluation/sessions/<pk>/instructions/` | instructions_list | instructions/list.html | Instructions for session |
| accept_instruction | `/evaluation/instructions/<inst_pk>/accept/` | accept_instruction | - | Accept instruction |
| reject_instruction | `/evaluation/instructions/<inst_pk>/reject/` | reject_instruction | - | Reject instruction |

### 5.6 Requirements

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| requirements_list | `/evaluation/sessions/<pk>/requirements/` | requirements_list | requirements/list.html | Requirements for session |
| satisfy_requirement | `/evaluation/requirements/<req_pk>/satisfy/` | satisfy_requirement | - | Satisfy requirement |

### 5.7 Engineer Review & Workflow

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| engineer_review | `/evaluation/sessions/<pk>/review/` | engineer_review | review/engineer.html | Engineer review |
| approve_session | `/evaluation/sessions/<pk>/approve/` | approve_session | - | Approve session |
| lock_session | `/evaluation/sessions/<pk>/lock/` | lock_session | - | Lock session |

### 5.8 Printing & History

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| print_job_card | `/evaluation/sessions/<pk>/print/` | print_job_card | print/job_card.html | Print job card |
| print_summary | `/evaluation/sessions/<pk>/print/summary/` | print_summary | print/summary.html | Print summary |
| history_view | `/evaluation/sessions/<pk>/history/` | history_view | history/timeline.html | View history |

### 5.9 Evaluation Settings

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| settings | `/evaluation/settings/` | settings_dashboard | settings/dashboard.html | Evaluation settings |
| code_list | `/evaluation/settings/codes/` | CodeListView | settings/codes_list.html | Codes list |
| feature_list | `/evaluation/settings/features/` | FeatureListView | settings/features_list.html | Features list |
| section_list | `/evaluation/settings/sections/` | SectionListView | settings/sections_list.html | Sections list |
| type_list | `/evaluation/settings/types/` | TypeListView | settings/types_list.html | Types list |
| instruction_template_list | `/evaluation/settings/instruction-templates/` | InstructionTemplateListView | - | Instruction templates |
| requirement_template_list | `/evaluation/settings/requirement-templates/` | RequirementTemplateListView | - | Requirement templates |

---

## 6. HR APP

**Namespace:** `hr`
**Base URL:** `/hr/`
**URLs File:** `floor_app/operations/hr/urls.py`
**Templates:** `floor_app/operations/hr/templates/hr/`
**App Name in URLs:** `hr`

### 6.1 Dashboard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| dashboard | `/hr/` | hr_dashboard | hr_dashboard.html | **HR dashboard** |
| dashboard_stats | `/hr/api/stats/` | dashboard_stats | - | Dashboard stats API |

### 6.2 Employee Portal & Wizard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| employee_portal | `/hr/portal/` | employee_portal | employee_portal.html | Employee self-service portal |
| employee_wizard_start | `/hr/employee/wizard/` | employee_wizard_start | employee_wizard_person.html | Employee wizard - start |
| employee_wizard_contact | `/hr/employee/wizard/contact/` | employee_wizard_contact | employee_wizard_contact.html | Wizard - contact step |
| employee_wizard_employee | `/hr/employee/wizard/employee/` | employee_wizard_employee | employee_wizard_employee.html | Wizard - employee step |
| employee_wizard_review | `/hr/employee/wizard/review/` | employee_wizard_review | employee_wizard_review.html | Wizard - review step |

### 6.3 People Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| people_list | `/hr/people/` | people_list | people_list.html | People directory |
| person_create | `/hr/people/create/` | person_create | person_form.html | Create person |
| person_detail | `/hr/people/<pk>/` | person_detail | person_detail.html | Person details |
| person_edit | `/hr/people/<pk>/edit/` | person_edit | person_form.html | Edit person |
| person_delete | `/hr/people/<pk>/delete/` | person_delete | confirm_delete.html | Delete person |
| people_search | `/hr/people/search/` | people_list | people_list.html | Search people |

### 6.4 Employee Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| employee_list | `/hr/employees/` | employee_list | employee_list.html | Employees list |
| employee_active | `/hr/employees/active/` | employee_active | employee_list.html | Active employees |
| employee_detail | `/hr/employees/<pk>/` | employee_detail | employee_detail.html | Employee details |
| employee_edit | `/hr/employees/<pk>/edit/` | employee_edit | employee_form.html | Edit employee |
| employee_import | `/hr/employees/import/` | employee_import | employee_import.html | Import employees |
| employee_export | `/hr/employees/export/` | employee_export | - | Export employees |

### 6.5 Contact Information

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| phone_list | `/hr/phones/` | phone_list | phone_list.html | Phones list |
| phone_bulk_add | `/hr/phones/bulk-add/` | phone_bulk_add | phone_bulk_add.html | Bulk add phones |
| email_list | `/hr/emails/` | email_list | email_list.html | Emails list |
| email_bulk_add | `/hr/emails/bulk-add/` | email_bulk_add | email_bulk_add.html | Bulk add emails |
| address_list | `/hr/addresses/` | address_list | address_list.html | Addresses list |
| address_add | `/hr/addresses/add/` | address_add | address_form.html | Add address |
| address_detail | `/hr/addresses/<pk>/` | address_detail | address_detail.html | Address details |
| address_edit | `/hr/addresses/<pk>/edit/` | address_edit | address_form.html | Edit address |
| address_delete | `/hr/addresses/<pk>/delete/` | address_delete | confirm_delete.html | Delete address |

### 6.6 Organizational Structure

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| department_list | `/hr/departments/` | DepartmentListView | department_list.html | Departments list |
| department_create | `/hr/departments/create/` | DepartmentCreateView | department_form.html | Create department |
| department_detail | `/hr/departments/<pk>/` | DepartmentDetailView | department_detail.html | Department details |
| department_update | `/hr/departments/<pk>/edit/` | DepartmentUpdateView | department_form.html | Edit department |
| department_delete | `/hr/departments/<pk>/delete/` | DepartmentDeleteView | department_confirm_delete.html | Delete department |
| position_list | `/hr/positions/` | PositionListView | position_list.html | Positions list |
| position_create | `/hr/positions/create/` | PositionCreateView | - | Create position |
| position_detail | `/hr/positions/<pk>/` | PositionDetailView | - | Position details |
| position_update | `/hr/positions/<pk>/edit/` | PositionUpdateView | - | Edit position |
| position_delete | `/hr/positions/<pk>/delete/` | PositionDeleteView | - | Delete position |

### 6.7 Leave Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| leave_policy_list | `/hr/leave/policies/` | LeavePolicyListView | - | Leave policies |
| leave_policy_create | `/hr/leave/policies/create/` | LeavePolicyCreateView | - | Create leave policy |
| leave_policy_detail | `/hr/leave/policies/<pk>/` | LeavePolicyDetailView | - | Leave policy details |
| leave_policy_edit | `/hr/leave/policies/<pk>/edit/` | LeavePolicyUpdateView | - | Edit leave policy |
| leave_balance_dashboard | `/hr/leave/balances/` | leave_balance_dashboard | - | Leave balances |
| leave_balance_adjust | `/hr/leave/balances/<pk>/adjust/` | leave_balance_adjust | - | Adjust leave balance |
| leave_balance_initialize | `/hr/leave/balances/initialize/` | leave_balance_initialize | - | Initialize balances |
| leave_request_list | `/hr/leave/requests/` | LeaveRequestListView | - | Leave requests |
| leave_request_create | `/hr/leave/requests/create/` | LeaveRequestCreateView | - | Create leave request |
| leave_request_detail | `/hr/leave/requests/<pk>/` | LeaveRequestDetailView | - | Leave request details |
| leave_request_submit | `/hr/leave/requests/<pk>/submit/` | leave_request_submit | - | Submit leave request |
| leave_request_approve | `/hr/leave/requests/<pk>/approve/` | leave_request_approve | - | Approve leave request |
| leave_request_cancel | `/hr/leave/requests/<pk>/cancel/` | leave_request_cancel | - | Cancel leave request |
| leave_calendar | `/hr/leave/calendar/` | leave_calendar | - | Leave calendar |
| my_leave_dashboard | `/hr/leave/my-dashboard/` | my_leave_dashboard | - | My leave dashboard |

### 6.8 Document Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| my_documents_dashboard | `/hr/documents/my-documents/` | my_documents_dashboard | - | My documents |
| employee_upload_document | `/hr/documents/upload/` | employee_upload_document | - | Upload document |
| employee_view_document | `/hr/documents/<pk>/view/` | employee_view_document | - | View document |
| employee_request_renewal | `/hr/documents/<pk>/request-renewal/` | employee_request_renewal | - | Request renewal |
| hr_documents_dashboard | `/hr/documents/hr/` | hr_documents_dashboard | - | HR documents |
| hr_upload_document | `/hr/documents/hr/upload/` | hr_upload_document | - | HR upload document |
| hr_expiry_dashboard | `/hr/documents/hr/expiry/` | hr_expiry_dashboard | - | Expiring documents |
| hr_document_detail | `/hr/documents/hr/<pk>/` | hr_document_detail | - | HR document details |
| hr_verify_document | `/hr/documents/hr/<pk>/verify/` | hr_verify_document | - | Verify document |
| hr_bulk_actions | `/hr/documents/hr/bulk-actions/` | hr_bulk_actions | - | Bulk actions |
| print_document_list | `/hr/documents/hr/print/` | print_document_list | - | Print document list |

### 6.9 Attendance & Overtime

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| attendance_dashboard | `/hr/attendance/` | attendance_dashboard | - | Attendance dashboard |
| attendance_list | `/hr/attendance/list/` | attendance_list | - | Attendance records |
| attendance_entry | `/hr/attendance/entry/` | attendance_entry | - | Attendance entry |
| punch_machine_import | `/hr/attendance/import/` | punch_machine_import | - | Import punch data |
| export_attendance_csv | `/hr/attendance/export/` | export_attendance_csv | - | Export attendance |
| attendance_report | `/hr/attendance/reports/` | attendance_report | - | Attendance report |
| overtime_request_list | `/hr/overtime/` | overtime_request_list | - | Overtime requests |
| overtime_request_create | `/hr/overtime/request/` | overtime_request_create | - | Create overtime request |
| overtime_request_detail | `/hr/overtime/<pk>/` | overtime_request_detail | - | Overtime details |
| overtime_request_approve | `/hr/overtime/<pk>/approve/` | overtime_request_approve | - | Approve overtime |
| delay_incident_list | `/hr/delays/` | delay_incident_list | - | Delay incidents |
| delay_incident_report | `/hr/delays/report/` | delay_incident_report | - | Delay report |
| delay_incident_review | `/hr/delays/<pk>/review/` | delay_incident_review | - | Review delay |

### 6.10 Training

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| training_program_list | `/hr/training/programs/` | TrainingProgramListView | - | Training programs |
| training_program_create | `/hr/training/programs/create/` | TrainingProgramCreateView | - | Create training program |
| training_program_detail | `/hr/training/programs/<pk>/` | TrainingProgramDetailView | - | Training program details |
| training_program_edit | `/hr/training/programs/<pk>/edit/` | TrainingProgramUpdateView | - | Edit training program |
| training_session_list | `/hr/training/sessions/` | TrainingSessionListView | - | Training sessions |
| training_session_create | `/hr/training/sessions/create/` | TrainingSessionCreateView | - | Create training session |
| training_session_detail | `/hr/training/sessions/<pk>/` | TrainingSessionDetailView | - | Training session details |
| training_session_edit | `/hr/training/sessions/<pk>/edit/` | TrainingSessionUpdateView | - | Edit training session |
| training_enroll | `/hr/training/sessions/<session_id>/enroll/` | enroll_employees | - | Enroll employees |
| my_training_dashboard | `/hr/training/my-training/` | my_training_dashboard | - | My training |
| training_complete | `/hr/training/complete/<pk>/` | complete_training | - | Complete training |
| training_feedback | `/hr/training/feedback/<pk>/` | submit_feedback | - | Submit training feedback |

### 6.11 HR Reports & Settings

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| reports | `/hr/reports/` | reports | reports.html | HR reports |
| settings | `/hr/settings/` | settings | settings.html | HR settings |

### 6.12 HR APIs

| URL Name | Full URL | View | Description |
|----------|----------|------|-------------|
| person_search_api | `/hr/api/people/search/` | person_search_api | Person search API |
| person_detail_api | `/hr/api/people/<person_id>/` | person_detail_api | Person details API |
| person_create_ajax | `/hr/api/people/create/` | person_create_ajax | Create person AJAX |
| person_contacts_api | `/hr/api/people/<person_id>/contacts/` | person_contacts_api | Person contacts API |
| save_contacts_ajax | `/hr/api/contacts/save/` | save_contacts_ajax | Save contacts AJAX |
| convert_date | `/hr/api/convert-date/` | convert_date | Convert date API |
| save_employee_ajax | `/hr/api/employee/save/` | save_employee_ajax | Save employee AJAX |
| position_list_api | `/hr/positions/api/` | position_list_api | Positions API |
| department_list_api | `/hr/api/departments/` | department_list_api | Departments API |
| employee_list_api | `/hr/api/employees/` | employee_list_api | Employees API |

---

## 7. INVENTORY APP

**Namespace:** `inventory`
**Base URL:** `/inventory/`
**URLs File:** `floor_app/operations/inventory/urls.py`
**Templates:** `floor_app/operations/inventory/templates/inventory/`
**App Name in URLs:** `inventory`

### 7.1 Dashboard

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| dashboard | `/inventory/` | dashboard | dashboard.html | **Inventory dashboard** |

### 7.2 Item Master

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| item_list | `/inventory/items/` | ItemListView | - | Items list |
| item_create | `/inventory/items/create/` | ItemCreateView | - | Create item |
| item_detail | `/inventory/items/<pk>/` | ItemDetailView | - | Item details |
| item_edit | `/inventory/items/<pk>/edit/` | ItemUpdateView | - | Edit item |

### 7.3 Bit Designs

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| bitdesign_list | `/inventory/bit-designs/` | BitDesignListView | - | Bit designs list |
| bitdesign_create | `/inventory/bit-designs/create/` | BitDesignCreateView | - | Create bit design |
| bitdesign_detail | `/inventory/bit-designs/<pk>/` | BitDesignDetailView | - | Bit design details |
| bitdesign_edit | `/inventory/bit-designs/<pk>/edit/` | BitDesignUpdateView | - | Edit bit design |

### 7.4 MAT Revisions

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| mat_list | `/inventory/mats/` | BitDesignRevisionListView | - | MAT revisions list |
| mat_create | `/inventory/mats/create/` | BitDesignRevisionCreateView | - | Create MAT revision |
| mat_detail | `/inventory/mats/<pk>/` | BitDesignRevisionDetailView | - | MAT revision details |
| mat_edit | `/inventory/mats/<pk>/edit/` | BitDesignRevisionUpdateView | - | Edit MAT revision |

### 7.5 Locations

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| location_list | `/inventory/locations/` | LocationListView | - | Locations list |
| location_create | `/inventory/locations/create/` | LocationCreateView | - | Create location |
| location_detail | `/inventory/locations/<pk>/` | LocationDetailView | - | Location details |
| location_edit | `/inventory/locations/<pk>/edit/` | LocationUpdateView | - | Edit location |

### 7.6 Serial Units

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| serialunit_list | `/inventory/serial-units/` | SerialUnitListView | - | Serial units list |
| serialunit_create | `/inventory/serial-units/create/` | SerialUnitCreateView | - | Create serial unit |
| serial_unit_create | `/inventory/serial-units/create/` | SerialUnitCreateView | - | Create serial unit (alias) |
| serialunit_detail | `/inventory/serial-units/<pk>/` | SerialUnitDetailView | - | Serial unit details |
| serialunit_edit | `/inventory/serial-units/<pk>/edit/` | SerialUnitUpdateView | - | Edit serial unit |

### 7.7 Stock Management

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| stock_list | `/inventory/stock/` | InventoryStockListView | - | Stock overview |
| stock_detail | `/inventory/stock/<pk>/` | InventoryStockDetailView | - | Stock details |
| stock_adjust | `/inventory/stock/adjust/` | stock_adjustment | - | Stock adjustment |
| stock_adjustment_create | `/inventory/stock/adjust/create/` | stock_adjustment | - | Stock adjustment (alias) |

### 7.8 Bill of Materials (BOM)

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| bom_list | `/inventory/boms/` | BOMListView | - | BOMs list |
| bom_create | `/inventory/boms/create/` | BOMCreateView | - | Create BOM |
| bom_detail | `/inventory/boms/<pk>/` | BOMDetailView | - | BOM details |
| bom_edit | `/inventory/boms/<pk>/edit/` | BOMUpdateView | - | Edit BOM |

### 7.9 Transactions

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| transaction_list | `/inventory/transactions/` | TransactionListView | - | Transactions list |
| transaction_detail | `/inventory/transactions/<pk>/` | TransactionDetailView | - | Transaction details |
| transaction_create | `/inventory/transactions/create/` | transaction_create | - | Create transaction |

### 7.10 Inventory Settings

| URL Name | Full URL | View | Template | Description |
|----------|----------|------|----------|-------------|
| settings | `/inventory/settings/` | settings_dashboard | - | Inventory settings |
| condition_list | `/inventory/settings/conditions/` | ConditionTypeListView | - | Condition types |
| ownership_list | `/inventory/settings/ownership/` | OwnershipTypeListView | - | Ownership types |
| category_list | `/inventory/settings/categories/` | ItemCategoryListView | - | Item categories |
| uom_list | `/inventory/settings/uom/` | UOMListView | - | Units of measure |

---

## 8. OTHER MAJOR APPS (Summary)

### 8.1 PLANNING APP

**Namespace:** `planning`
**Base URL:** `/planning/`

Key features:
- Resources & Capacity Planning
- Production Schedules
- KPI Dashboard & Definitions
- WIP Board
- Forecasting & At-Risk Jobs
- OTD & Utilization Reports

### 8.2 MAINTENANCE APP

**Namespace:** `maintenance`
**Base URL:** `/maintenance/`

Key features:
- Asset Management
- Maintenance Requests
- Work Orders
- Preventive Maintenance (PM)
- Downtime Tracking
- QR Code Asset Links

### 8.3 PURCHASING APP

**Namespace:** `purchasing`
**Base URL:** `/purchasing/`

Key features:
- Supplier Management
- Purchase Requisitions (PR)
- Purchase Orders (PO)
- Goods Receipt Notes (GRN)
- Supplier Invoices & 3-Way Matching
- Internal Transfers
- Outbound Shipments
- Customer Returns

### 8.4 SALES APP

**Namespace:** `sales`
**Base URL:** `/sales/`

Key features:
- Customer & Rig Management
- Wells & Opportunities
- Sales Orders
- Bit Lifecycle Timeline
- Drilling Runs & Dull Grades
- Shipments & Junk Sales

### 8.5 KNOWLEDGE APP

**Namespace:** `knowledge`
**Base URL:** `/knowledge/`

Key features:
- Articles & Procedures
- Business Instructions
- Document Library
- Training Courses & Schedules
- FAQ Management
- Global Search

### 8.6 QRCODES APP

**Namespace:** `qrcodes`
**Base URL:** `/qrcodes/`

Key features:
- QR Code Generation
- Central Scan Handler
- Equipment Tracking
- Container Management
- Maintenance Reporting via QR
- BOM Material Pickup/Return
- Movement Logs

### 8.7 ANALYTICS APP

**Namespace:** `analytics`
**Base URL:** `/analytics/`

Key features:
- User Activity Tracking
- Session Monitoring
- Error Logs
- Module Usage Statistics
- Realtime Analytics
- User Reports & Exports

---

## 9. TEMPLATE CLEANUP STATUS

### 9.1 Clean Apps (No Duplicates) ✅

- **production** - All templates in `floor_app/operations/production/templates/production/`
- **evaluation** - All templates in `floor_app/operations/evaluation/templates/evaluation/`
- **core** - All templates in `core/templates/core/`

### 9.2 Cleaned Apps (Duplicates Removed) ✅

- **hr** - Removed ~35 duplicate templates from `floor_app/templates/hr/` (Phase 1.1)
- **quality** - Removed ~20 duplicate templates from `floor_app/templates/quality/` (Phase 1.1)
- **knowledge** - Removed ~10 duplicate templates from `floor_app/templates/knowledge/` (Phase 1.1)

### 9.3 Template Loading Priority

Django searches for templates in this order:
1. App-specific `templates/` directories (based on `INSTALLED_APPS` order)
2. Directories listed in `TEMPLATES['DIRS']` setting

Current correct locations:
- `floor_app/operations/<app>/templates/<app>/`
- `core/templates/core/`

---

## 10. URL NAMING STANDARDS

### 10.1 Namespace Pattern
```
<app_name>:<url_name>
```

Examples:
- `core:home`
- `production:dashboard`
- `quality:ncr_list`
- `hr:employee_detail`
- `inventory:item_create`

### 10.2 Common URL Name Conventions

| Action | Pattern | Example |
|--------|---------|---------|
| Dashboard | `<app>:dashboard` | `production:dashboard` |
| List | `<app>:<entity>_list` | `quality:ncr_list` |
| Create | `<app>:<entity>_create` | `inventory:item_create` |
| Detail | `<app>:<entity>_detail` | `hr:employee_detail` |
| Edit/Update | `<app>:<entity>_edit` or `<entity>_update` | `production:batch_edit` |
| Delete | `<app>:<entity>_delete` | `hr:person_delete` |
| Settings | `<app>:settings` | `quality:settings` |

### 10.3 Fixed URL Name Conflicts (Phase 1.2) ✅

| App | Old URL Name | New URL Name | Status |
|-----|--------------|--------------|--------|
| evaluation | `settings_dashboard` | `settings` | ✅ Fixed |
| quality | `settings_dashboard` | `settings` | ✅ Fixed |
| planning | `settings_dashboard` | `settings` | ✅ Fixed |
| inventory | `settings_dashboard` (alias) | (removed alias) | ✅ Fixed |

---

## 11. KNOWN ISSUES & FIXES

### 11.1 ✅ FIXED: Production Dashboard Cards (Phase 1.3)

**Issue:** All dashboard cards were pointing to wrong pages
**Fix:** Created 4 new global list views and updated dashboard template

| Card | Old URL | New URL | Status |
|------|---------|---------|--------|
| Evaluations | `evaluation:session_list` (wrong app!) | `production:evaluation_list_all` | ✅ Fixed |
| NDT Inspections | `evaluation:session_list` (wrong app!) | `production:ndt_list_all` | ✅ Fixed |
| Thread Inspections | `production:jobcard_list` (wrong page) | `production:thread_inspection_list_all` | ✅ Fixed |
| Checklists | `production:jobcard_list` (wrong page) | `production:checklist_list_all` | ✅ Fixed |

**Files Modified:**
- `floor_app/operations/production/views.py` (added 4 new ListView classes)
- `floor_app/operations/production/urls.py` (added 4 new URL patterns)
- `floor_app/operations/production/templates/production/dashboard.html` (updated card URLs)

### 11.2 ✅ FIXED: Template Duplicates (Phase 1.1)

**Issue:** 60+ duplicate templates causing confusion
**Fix:** Removed all duplicates from `floor_app/templates/`

**Deleted:**
- `floor_app/templates/hr/` (35 templates)
- `floor_app/templates/quality/` (20 templates)
- `floor_app/templates/knowledge/` (13 templates)
- `floor_app/templates/production/dashboard.html` (1 template)

### 11.3 ✅ FIXED: URL Name Conflicts (Phase 1.2)

**Issue:** Multiple apps using same URL name causing routing errors
**Fix:** Standardized all settings URLs to use `settings` instead of `settings_dashboard`

**Modified Files:**
- `floor_app/operations/evaluation/urls.py`
- `floor_app/operations/inventory/urls.py`
- `floor_app/operations/quality/urls.py`
- `floor_app/operations/planning/urls.py`

---

## 12. MAINTENANCE GUIDELINES

### 12.1 When Adding New URLs

1. **Always use namespaces** in root `floor_mgmt/urls.py`:
   ```python
   path("myapp/", include(("floor_app.operations.myapp.urls", "myapp"), namespace="myapp")),
   ```

2. **Define `app_name` in app's `urls.py`**:
   ```python
   app_name = "myapp"
   ```

3. **Use consistent URL naming**:
   - Dashboard: `dashboard`
   - Lists: `<entity>_list`
   - Create: `<entity>_create`
   - Detail: `<entity>_detail`
   - Edit: `<entity>_edit` or `<entity>_update`
   - Delete: `<entity>_delete`

### 12.2 When Creating Templates

1. **Always use app-specific directory**:
   ```
   floor_app/operations/<app>/templates/<app>/
   ```

2. **Never create templates in**:
   ```
   floor_app/templates/<app>/  ❌ WRONG
   ```

3. **Use namespaced template names in views**:
   ```python
   template_name = 'production/dashboard.html'  # Not 'dashboard.html'
   ```

### 12.3 When Linking in Templates

1. **Always use namespaced URLs**:
   ```django
   <a href="{% url 'production:dashboard' %}">Dashboard</a>
   ```

2. **Never use hardcoded paths**:
   ```django
   <a href="/production/">Dashboard</a>  ❌ WRONG
   ```

3. **Use `url` tag with parameters**:
   ```django
   <a href="{% url 'production:batch_detail' pk=batch.id %}">View Batch</a>
   ```

---

## 13. REFERENCE: APP NAME → NAMESPACE → URL PREFIX

| App Name | Namespace | URL Prefix | URLs File |
|----------|-----------|-----------|-----------|
| core | core | / | core/urls.py |
| hr | hr | /hr/ | floor_app/operations/hr/urls.py |
| inventory | inventory | /inventory/ | floor_app/operations/inventory/urls.py |
| production | production | /production/ | floor_app/operations/production/urls.py |
| evaluation | evaluation | /evaluation/ | floor_app/operations/evaluation/urls.py |
| quality | quality | /quality/ | floor_app/operations/quality/urls.py |
| purchasing | purchasing | /purchasing/ | floor_app/operations/purchasing/urls.py |
| maintenance | maintenance | /maintenance/ | floor_app/operations/maintenance/urls.py |
| planning | planning | /planning/ | floor_app/operations/planning/urls.py |
| sales | sales | /sales/ | floor_app/operations/sales/urls.py |
| knowledge | knowledge | /knowledge/ | floor_app/operations/knowledge/urls.py |
| qrcodes | qrcodes | /qrcodes/ | floor_app/operations/qrcodes/urls.py |
| analytics | analytics | /analytics/ | floor_app/operations/analytics/urls.py |

---

## Document Version

**Version:** 1.0
**Created:** 2025-11-22
**Last Updated:** 2025-11-22
**Branch:** cleanup/navigation-fix
**Prepared By:** Claude Code AI Assistant

**Related Documents:**
- `docs/routing_xray_summary.md` - Analysis of routing issues
- `docs/template_duplicates_report.md` - Template duplication analysis
- `docs/PHASE_1_COMPLETION_REPORT.md` - Phase 1 fixes summary
- `docs/url_name_inventory.md` - URL name conflict analysis
- `docs/routing_map_production_dashboard.md` - Production dashboard routing
- `docs/routing_map_quality_features.md` - Quality features routing

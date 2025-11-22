# Floor Management System – MASTER BUILD SPEC (Version C – Detailed)

You are building the **Floor Management System (FMS)** for a **drilling bit production & repair workshop** (PDC & roller-cone bits).

This document is your **constitution**.
Everything you do in `Floor-Management-System` must follow this spec.

- Old repo **B** = `Ramzi-Kassab/Floor-Management-System` → **read-only reference**
- New Branch = `Ramzi-Kassab/Floor-Management-System/new-build` → **active build**

If old code conflicts with *this* file, this file wins.

---

## 0. HIGH-LEVEL GOAL

We want one web system that:

- Tracks **bits** (design, MAT, BOM, serial, lifecycle).
- Manages **production & repair** (work orders, job cards, routes, timing, operators).
- Handles **evaluation & QC** (NDT, thread inspection, cutter evaluation, die checks).
- Manages **HR & admin** (employees, attendance, leaves, training, assets).
- Handles **inventory** (items, cutters, consumables, ownership, condition, stock).
- Supports **planning & scheduling**, **QR tracking**, **notifications**, and **analytics**.

Key qualities:

- **One unified skeleton** (auth, layout, navigation).
- **Modular apps** by domain.
- **No duplicated models or templates**.
- **PostgreSQL-first** (indexes & constraints).
- **Traceable** (logging, notifications, audit) but can start simple.

---

## 1. TECHNOLOGY

- Python 3.10+
- Django 5.2.x
- PostgreSQL (dev & prod)
- Django REST Framework
- Bootstrap 5 (via CDN) for styling
- Optional HTMX/jQuery for interactivity
- GitHub Codespaces for dev
- Docker/Docker Compose (later, for deployment)

Environment expectations:

- The project root is `Floor-Management-System`.
- Django project (settings) is already created (e.g., `floor_mgmt`).
- Database is e.g. `floor_management_c`.

---

## 2. APP ARCHITECTURE

### 2.1 Foundational Apps

#### 2.1.1 `core_foundation` (ALREADY EXISTS, MUST REMAIN THE FOUNDATION)

Purpose: **shared foundational models** that many apps depend on, but which do not depend on project domain apps.

Core models (typical fields):

1. **CostCenter**
   - `code` (CharField, unique, e.g. "PDC-01")
   - `name` (CharField)
   - `description` (TextField, optional)
   - `is_active` (BooleanField, default True)

2. **Currency**
   - `code` (CharField, "USD", "SAR")
   - `name` (CharField)
   - `symbol` (CharField, "$", "ر.س")
   - `is_default` (BooleanField)

3. **ExchangeRate**
   - `from_currency` (FK → Currency)
   - `to_currency` (FK → Currency)
   - `rate` (DecimalField, 12,6)
   - `valid_from` (DateTime)
   - Unique constraint on `(from_currency, to_currency, valid_from)`.

4. **ApprovalType**
   - `code` ("LEAVE_APPROVAL", "PURCHASE_APPROVAL")
   - `name`
   - `description`
   - `is_active`

5. **ApprovalAuthority**
   - `approval_type` (FK → ApprovalType)
   - `role_or_employee` (for now simple CharField; later link to HREmployee / Groups)
   - `sequence` (Integer, order in chain)
   - `is_final` (Boolean)

6. **ERPReference**
   - GenericFK: `content_type`, `object_id`
   - `erp_system` (CharField: "SAP", "Dynamics")
   - `erp_document_type` (CharField: "PO", "SO", "WO")
   - `erp_document_number` (CharField)
   - `extra_data` (JSONField)

7. **LossOfSaleEvent** (finance-heavy but keep it; can be hidden in UI)
   - GenericFK to the object that caused loss (e.g., stock-out, delay)
   - `description`
   - `estimated_loss_value` (Decimal)
   - `currency` (FK → Currency)
   - `date`
   - `reason_category` (choice field: "late_delivery", "quality_issue", etc.)

8. **Notification**
   - `recipient` (FK → auth.User)
   - Optional GenericFK to target object
   - `title`
   - `message`
   - `level` (choice: info, warning, success, danger)
   - `is_read` (Boolean)
   - `created_at`

9. **ActivityLog**
   - Optional GenericFK to target object
   - `actor` (FK → auth.User, nullable)
   - `action` (CharField: "CREATE", "UPDATE", "DELETE", "APPROVE", etc.)
   - `description`
   - `extra_data` (JSONField)
   - `timestamp`

10. **UserPreference**
    - OneToOne → auth.User (primary key)
    - `theme` (light/dark)
    - `table_density` (comfortable/compact)
    - `default_landing_page` (CharField: "dashboard", "hr_portal", etc.)
    - `sidebar_collapsed` (Boolean)

Design Constraints:

- **No FK** from `core_foundation` to HR, inventory, etc.
- Use `ContentType` for polymorphic needs (ERPReference, ActivityLog, Notification).
- Keep db_table names aligned with old repo where sensible.

---

#### 2.1.2 `skeleton` / `accounts` / `core_dashboard` (NAME YOU CHOOSE, BUT BE CONSISTENT)

This app (or combination of `core` + templates) is the **global skeleton**:

Responsibilities:

- Authentication:
  - `/login/`
  - `/logout/`
  - `/password_change/` + done
  - `/password_reset/` + done + confirm + complete

- Global layout:
  - `templates/base.html` (main layout)
  - `templates/base_auth.html` (simplified auth layout)
  - `templates/partials/_navbar.html`
  - `templates/partials/_sidebar.html` (optional)
  - `templates/partials/_messages.html`

- Home/dashboard:
  - `/`:
    - If not logged in → simple landing page "FMS" + Login button.
    - If logged in → redirect to `/dashboard/`.
  - `/dashboard/`:
    - Shows cards for: HR, Portal, Inventory, Engineering, Production, Evaluation, Quality.
    - Shows simple KPIs:
      - e.g. "Open Job Cards", "Pending Leave Requests", "Low Stock Items" (even as placeholders).
    - Later can use `ActivityLog` for recent activity.

- Error pages:
  - `/templates/404.html`
  - `/templates/403.html`
  - `/templates/500.html`
  - All extend `base.html`.

- "My Account":
  - `/account/profile/`:
    - Show info from `auth.User` and link to HR employee if exists.
  - `/account/settings/`:
    - For now, link to "Change password" and show some `UserPreference`.

Authentication Implementation:

- Use Django auth CBVs:
  - `django.contrib.auth.views.LoginView`, etc.
- Templates under `templates/accounts/…`:
  - `login.html`
  - `password_change_form.html`
  - `password_change_done.html`
  - `password_reset_form.html`
  - `password_reset_done.html`
  - `password_reset_confirm.html`
  - `password_reset_complete.html`
- All extend `base_auth.html` or `base.html`.

---

### 2.2 HR & Administration

We separate:

- `hr` → HR back-office (HR & Admin team)
- `hr_portal` → Employee self-service portal

#### 2.2.1 `hr` (Back-Office, ALREADY MODELED)

Models (from previous HR design, refine but stay close):

1. **HRPerson**
   - `first_name`
   - `last_name`
   - `middle_name` (optional)
   - `national_id` / `iqama` / `passport_no`
   - `date_of_birth`
   - `nationality`
   - `gender`
   - `contact_phone_primary`
   - `contact_email_primary`
   - Relationship: can be linked to auth.User (optional)

2. **HREmployee**
   - FK → HRPerson (1:1)
   - `employee_code` (unique, e.g. "E-00123")
   - `status` (active, on_leave, resigned, terminated)
   - `department` (FK → Department)
   - `position` (FK → Position)
   - `joining_date`
   - `leaving_date` (nullable)
   - `cost_center` (FK → CostCenter)
   - `is_qc`, `is_production`, `is_planning` (Booleans) if useful

3. **Department**
   - `code`
   - `name`
   - `description`
   - `parent_department` (self FK, nullable)

4. **Position**
   - `code`
   - `title`
   - `department` (FK)
   - `description`
   - `is_supervisory` (Boolean)

5. **HRContract**
   - FK → HREmployee
   - `contract_type` (permanent, temporary, contractor)
   - `start_date`
   - `end_date`
   - `basic_salary`
   - `housing_allowance`
   - `transport_allowance`
   - `other_allowances`
   - `currency` (FK → Currency)
   - `is_current` (Boolean)
   - These fields show in **Finance panel** in UI (collapsible/permission-based).

6. **HRShiftTemplate**
   - `name` (e.g. "Day Shift", "Night Shift")
   - `start_time`
   - `end_time`
   - `is_night_shift` (Boolean)
   - `working_days` (JSON or choices mask)

7. **LeaveType**
   - `code`
   - `name` (Annual, Sick, Unpaid, etc.)
   - `requires_approval` (Boolean)
   - `max_days_per_year` (optional)
   - `is_paid` (Boolean)

8. **LeaveRequest**
   - FK → HREmployee
   - `leave_type`
   - `start_date`
   - `end_date`
   - `reason`
   - `status` (draft, submitted, approved, rejected, cancelled)
   - `approved_by` (FK → HREmployee or auth.User, nullable)
   - `approved_at`
   - Link to `ApprovalType` / workflow later.

9. **AttendanceRecord**
   - FK → HREmployee
   - `date`
   - `check_in_time`
   - `check_out_time`
   - `status` (present, absent, late, leave)
   - `details` (Text)

10. **TrainingProgram**
    - `code`
    - `title`
    - `description`
    - `provider`
    - `internal_or_external` (choice)

11. **TrainingSession**
    - FK → TrainingProgram
    - `start_date`
    - `end_date`
    - `location`
    - `instructor`

12. **EmployeeTraining**
    - FK → HREmployee
    - FK → TrainingSession
    - `status` (planned, attended, completed)
    - `score` (optional)

13. **QualificationLevel**
    - `code`
    - `name` (e.g., Level 1, Level 2 Brazing)
    - `description`

14. **EmployeeQualification**
    - FK → HREmployee
    - FK → QualificationLevel
    - `granted_date`
    - `expiry_date` (nullable)

15. **DocumentType**
    - `code`
    - `name` (e.g., "ID Copy", "Contract", "Certificate")
    - `description`

16. **EmployeeDocument**
    - FK → HREmployee
    - FK → DocumentType
    - `file` (FileField)
    - `uploaded_at`
    - `expires_at` (nullable)
    - `is_mandatory` (Boolean, for compliance)

17. **AssetType**
    - `code`
    - `name` (e.g., "Phone", "Vehicle", "Laptop", "Housing")
    - `description`

18. **HRAsset**
    - FK → AssetType
    - `asset_tag` (unique)
    - `description`
    - `serial_number`
    - `purchase_date`
    - `status` (available, assigned, maintenance, retired)
    - `cost_center` (FK → CostCenter)
    - Finance data as panel fields: `purchase_price`, `currency`.

19. **AssetAssignment**
    - FK → HRAsset
    - FK → HREmployee
    - `assigned_from`
    - `assigned_to`
    - `status` (active, returned)
    - `remarks`

20. **HRPhone**
    - FK → HREmployee
    - `phone_number`
    - `type` (mobile, work, home)
    - `is_primary` (Boolean)

21. **HREmail**
    - FK → HREmployee
    - `email`
    - `type` (work, personal)
    - `is_primary`

(If your previous Phase 2A branch has slightly different names, adapt them to this spec logically.)

##### HR Back-Office Views (Phase 2B)

Build fully working views & templates on top of skeleton:

- `/hr/` → HR home dashboard (list quick stats: employees count, open leave requests).
- `/hr/employees/` → list with filters (department, status).
- `/hr/employees/create/` → create HRPerson + HREmployee.
- `/hr/employees/<id>/` → detail page (personal, job, finance, documents, training, assets).
- `/hr/leaves/` → list of all leave requests.
- `/hr/leaves/<id>/approve/` → HR approval.
- `/hr/attendance/` → filter by date, department, etc.
- `/hr/training/` → programs & sessions list.

All templates in `hr/templates/hr/…` and extend `base.html`.

Permissions: only staff/HR roles can access `/hr/...` (we can start with `is_staff`).

---

#### 2.2.2 `hr_portal` (Employee Self-Service)

Models:

- **EmployeeRequest**
  - FK → HREmployee
  - `request_type` (choice: leave_request, document_request, general_service, etc.)
  - `title`
  - `description`
  - `status` (open, in_progress, closed)
  - `created_at`, `updated_at`
  - Later link to `Notification` and `ActivityLog`.

Portal Views:

- `/portal/` → portal dashboard (employee only):
  - Show: My profile summary, my leaves, my requests.
- `/portal/leaves/`:
  - List only the logged-in employee's LeaveRequest.
- `/portal/leaves/new/`:
  - Create leave request (no finance, simple).
- `/portal/requests/`:
  - My EmployeeRequests.
- `/portal/requests/new/`:
  - Create new request.
- `/portal/documents/`:
  - List `EmployeeDocument` for this employee (download links only).

All templates in `hr_portal/templates/hr_portal/…` and extend `base.html`.

Portal is for normal employees, not HR management.

---

### 2.3 Inventory

App: `inventory`

Core concepts:

- Items & categories
- Units
- Condition & ownership
- Locations & stock levels (by location, ownership, condition)
- Cutters and bit components (if not strictly engineering BOM)

Models (simplified target):

1. **ItemCategory**
   - `code`
   - `name`
   - `description`
   - `parent_category` (self FK, nullable)

2. **UnitOfMeasure**
   - `code` (e.g. "EA", "KG", "LTR")
   - `name`
   - `is_base_unit` (Boolean)

3. **Item**
   - `item_code` (unique)
   - `name`
   - `category` (FK)
   - `uom` (FK → UnitOfMeasure)
   - `description`
   - `is_active`
   - `is_stock_tracked` (Boolean)
   - `is_cutter` (Boolean) – for cutters
   - `is_upper_section` (Boolean) – for bit heads, etc.

4. **ConditionType**
   - `code` (e.g. NEW, USED, DAMAGED, SCRAP)
   - `name`
   - `description`

5. **OwnershipType**
   - `code` (e.g. "ARDT", "Customer", "Vendor")
   - `name`
   - `description`

6. **Location**
   - `code` (e.g. "MAIN-STORES", "PDC-FLOOR", "NDT-ROOM`)
   - `name`
   - `description`
   - `is_virtual` (Boolean)

7. **StockLevel**
   - FK → Item
   - FK → Location
   - FK → ConditionType
   - FK → OwnershipType
   - `quantity` (Decimal, 14,3)
   - Unique constraint on `(item, location, condition, ownership)`.

8. (Later) **StockTransaction**
   - `item`, `from_location`, `to_location`, `quantity`, `reason`, etc.

Inventory Views (Phase 3):

- `/inventory/items/` list + create + edit.
- `/inventory/stock/` list by location, filter by item, condition, ownership.
- `/inventory/cutters/` if needed as special filtered views.

Again: templates under `inventory/templates/inventory/…`.

---

### 2.4 Engineering (Bit Design & BOM)

App: `engineering`

Purpose: define **bit designs**, MAT numbers and BOMs.

Key domain facts (from Ramzi):

- Level 5 MAT = full bit (head + upper + cutters).
- Level 4 MAT = bit without cutters.
- Level 3 MAT = head and possibly pin.

Models:

1. **BitDesignType**
   - `code` (e.g. "PDC", "ROLLER_CONE")
   - `name`
   - `description`

2. **BitDesignLevel**
   - `level_number` (3, 4, 5)
   - `name` (e.g. "Head", "Head+Upper", "Complete Bit")
   - `description`

3. **BitDesign**
   - `design_code` (unique, e.g. "HD75WF")
   - `type` (FK → BitDesignType)
   - `level` (FK → BitDesignLevel)
   - `size_inch` (Decimal, 4,2)
   - `blade_count` (Integer, optional)
   - `description`
   - `is_active` (Boolean)

4. **BitDesignRevision**
   - FK → BitDesign
   - `revision_code` (e.g. "A0", "B2")
   - `mat_number` (CharField, unique)
   - `effective_from`
   - `effective_to` (nullable)
   - `is_active` (Boolean)
   - Unique **logical** constraint: `(bit_design, revision_code)`.

5. **BOMHeader**
   - `bom_number` (unique)
   - `target_type` (generic bit design or other)
   - For now: FK → BitDesignRevision (main use)
   - `bom_type` (manufacturing, repair)
   - `is_active`
   - `description`

6. **BOMLine**
   - FK → BOMHeader
   - `line_number` (Integer; unique per BOMHeader)
   - FK → Item (`component_item`)
   - `quantity` (Decimal)
   - `uom` (FK → UnitOfMeasure)
   - `required_condition` (FK → ConditionType)
   - `required_ownership` (FK → OwnershipType)
   - `is_optional` (Boolean)
   - Additional metadata: e.g. "location in bit" for cutters.

Engineering Views:

- `/engineering/designs/`
- `/engineering/designs/<id>/revisions/`
- `/engineering/boms/<id>/` (header + lines editor)
- All templates under `engineering/templates/engineering/…`.

---

### 2.5 Production

App: `production`

Goal: job cards & operations.

Models:

1. **WorkOrder**
   - `wo_number` (unique, e.g. "WO-2025-0001")
   - `customer` (FK → sales.Customer)
   - `rig` (FK → sales.Rig)
   - `well` (FK → sales.Well)
   - `bit_serial_number` (CharField: 8-digit + R1/R2 for repairs)
   - `mat_number` (FK → engineering.BitDesignRevision)
   - `order_type` (new_build, repair)
   - `status` (open, in_progress, completed, cancelled)
   - `received_date`
   - `due_date`
   - `remarks`

2. **JobCard**
   - `jobcard_number` (unique, e.g. "JC-2025-0012")
   - FK → WorkOrder
   - `status` (draft, planned, released, in_progress, paused, completed, cancelled)
   - `priority` (low, normal, high, urgent)
   - `planned_start`, `planned_end`
   - `actual_start`, `actual_end`
   - `current_station` (Text or FK to some station model later)
   - `qc_hold` (Boolean)
   - Link to evaluation: many-to-one from `EvaluationSession` or M2M, as needed.

3. **RouteStep**
   - FK → JobCard
   - `sequence` (Integer)
   - `process_code` (CharField, e.g. "GRIND", "BRAZE", "NDT")
   - `description`
   - `workstation` (CharField, or FK to a workstation)
   - `estimated_duration_min`
   - `actual_start`
   - `actual_end`
   - `status` (pending, in_progress, done, skipped)

4. **JobPause**
   - FK → JobCard
   - `start_time`
   - `end_time`
   - `reason` (e.g. waiting_material, waiting_qc, machine_breakdown)
   - `notes`

5. **AssignedOperator**
   - FK → JobCard
   - FK → HREmployee
   - `role` (e.g. "operator", "helper", "supervisor`)
   - `assigned_from`, `assigned_to`

6. **JobChecklistItem**
   - Master: checklist item definitions (e.g. for processes)
   - Link to JobCard: statuses, signatures, etc.

Views:

- `/production/jobcards/`
- `/production/jobcards/<id>/`
- `/production/jobcards/<id>/route/`
- `/production/jobcards/<id>/start/`, `/complete/`, `/pause/`.
- All templates under `production/templates/production/…`.

---

### 2.6 Evaluation (Unified Evaluation System)

App: `evaluation`

Goal: unify all evaluation & inspection:

- Cutter evaluation
- NDT
- Thread inspection
- Die check
- Optional: oil, flow, etc.

Key rule: **NO duplicate NDT/Thread models in production.** Only here.

Models:

1. **EvaluationSession**
   - `session_number` (string)
   - FK → JobCard (optional but desired)
   - FK → BitDesignRevision
   - `evaluation_date`
   - `evaluated_by` (FK → HREmployee or auth.User)
   - `status` (draft, in_progress, completed, approved)
   - `remarks`

2. **EvaluationCell** (generic rows for evaluation template)
   - FK → EvaluationSession
   - `position_code` (e.g. "B1", "C3" for cutter location)
   - `parameter` (e.g. "cutter_condition", "chipping", etc.)
   - `value_numeric`, `value_text` (flexible)
   - Optional `severity` (choice)

3. **NDTInspection**
   - FK → EvaluationSession
   - `ndt_method` (MPI, DPI, UT, etc.)
   - `result` (pass, fail, conditional)
   - `comments`

4. **ThreadInspection**
   - FK → EvaluationSession
   - `connection_type` (API, premium)
   - `damage_category` (none, minor, major)
   - `comments`
   - `api_gauge_result` (pass/fail), etc.

5. **DieCheckInspection**
   - FK → EvaluationSession
   - `die_number`
   - `result`
   - `comments`

Views:

- `/evaluation/sessions/`
- `/evaluation/sessions/<id>/`
- `/evaluation/sessions/<id>/grid/` for template/grid editor.
- `/evaluation/sessions/<id>/ndt/`
- `/evaluation/sessions/<id>/thread/`
- `/evaluation/sessions/<id>/print/` job card/evaluation summary.

Templates: `evaluation/templates/evaluation/…` with clear mapping to views.
**Fix any path mismatches** (like grid_editor etc.) according to spec; never reuse broken names from old code.

---

### 2.7 Quality, QR, Planning, Sales, Analytics, Knowledge

You already have high-level ideas. Here we just pin specifics.

#### 2.7.1 `quality`

- `NCR`
- `CalibrationRecord`
- `DefectType`
- Later integrate with Production/Evaluation.

#### 2.7.2 `qrcodes` (IMPORTANT, SHORT-TERM AFTER HR)

- `QRCode`
  - `code` (string encoded into QR)
  - GenericFK to target object
  - `created_at`
- Views:
  - `/qr/<code>/` → resolve & redirect to correct detail page (JobCard, Bit, Employee, Asset).
- Later: auto-generate QR codes in JobCard & HR asset pages.

#### 2.7.3 `planning`

- `PlanningScenario`
- `PlannedJob`
- Link to JobCard & resources.

#### 2.7.4 `sales`

- `Customer`, `Rig`, `Well`, `SalesOrder`, `RunRecord`.

#### 2.7.5 `analytics`

- `MetricDefinition`, `AutomationRule`, `ReportUsage`:
  - `ReportUsage` tracks:
    - report identifier
    - user
    - opened_at
    - duration (optional)
  - Use this to later build KPI "how many times report X is opened".

#### 2.7.6 `knowledge`

- `KnowledgeArticle`, `Procedure`, `TrainingMaterial`.

---

## 3. PHASED BUILD PLAN (FOR THIS AGENT)

You **build in repo C only**, reusing from repo B only when consistent with this spec.

### PHASE 1 – Foundation & Skeleton

1. Verify `core_foundation` models & migrations (fix if needed).
2. Build/complete skeleton app:
   - Auth views & templates.
   - `base.html`, `base_auth.html`, partials.
   - Home page & dashboard.
   - My Account pages.
   - Error pages.
3. Wire URLs:
   - root → skeleton urls.
   - include HR & hr_portal placeholders.

### PHASE 2 – HR & Administration

**Phase 2A** – HR models & admin (mostly done, just align names).
**Phase 2B** – HR Back-Office UI:

- Full CRUD for employees, leaves, attendance, training, assets.
- Use skeleton layout.
- Enforce HR-only access.

**Phase 2C** – HR Portal UI:

- Portal dashboard.
- My leaves.
- My requests.
- My documents.
- All filtered by logged-in employee.

After finishing HR & portal → **implement QR + Notifications wiring** (qrcodes & Notification usage) to "bring life" to the system.

### PHASE 3 – Inventory & Engineering

- Implement `inventory` models, views, templates as specified.
- Implement `engineering` BitDesign/BOM models & views.
- Ensure they use `core_foundation` + skeleton.

### PHASE 4 – Production & Evaluation

- Implement WorkOrder, JobCard, routes, checklists.
- Implement unified evaluation system with NDT, thread, die, cutter evaluation.
- Link JobCard ↔ EvaluationSession.

### PHASE 5 – Quality, Planning, Sales, Analytics, Knowledge

- Implement progressively, always using skeleton and rules above.

---

## 4. GIT & DOC RULES

- Use clear feature branches:
  - `feature/skeleton`
  - `feature/hr-backoffice`
  - `feature/hr-portal`
  - `feature/inventory`
  - etc.
- Each branch:
  - Implement one logical chunk of the spec.
  - `python manage.py check` must pass before push.
- Documentation:
  - This file: `docs/FMS_MASTER_BUILD_SPEC.md` (this document).
  - One PLAN + one SUMMARY per big phase.
  - Archive old noisy docs under `docs/archive/`.

---

## 5. AGENT BEHAVIOR RULES

1. **This file is the source of truth** – not old prompts.
2. **No fake phases** – don't call something Phase 3 if skeleton & HR UI aren't done.
3. **Be honest** in progress reports: say if templates are placeholders.
4. **Ask questions only when absolutely necessary** – otherwise make reasonable assumptions guided by this spec.
5. **Always test** (`check`, `migrate`, simple runserver) before claiming completion.
6. **Document decisions** in small docs like `docs/SKELETON_DECISIONS.md`.

---

## 6. STARTING INSTRUCTIONS FOR THE AGENT

1. Read this entire file (`docs/FMS_MASTER_BUILD_SPEC.md`).
2. Inspect current state of `Floor-Management-System`.
3. Determine current phase (likely: skeleton partially done, HR models present, HR UI incomplete).
4. Continue the build from the current state respecting the phases and details above.
5. For the next work chunk:
   - If skeleton/auth is incomplete → finish Phase 1.
   - Else → implement Phase 2B (HR back-office UI) and Phase 2C (HR Portal UI) consistent with this spec, then add QR & notifications entry points.

Each time you finish a chunk, report:

- What you implemented.
- Files changed.
- Commands run for testing.
- TODOs for next step.

---

## 🔧 GLOBAL SCOPE (Very Important)

For every app and feature in this document, the agent must implement:

### Database layer
- Django models with fields, constraints, indexes
- Migrations (makemigrations + migrate must pass)

### Back-end logic
- Views (class-based where possible)
- URL patterns with clear names + namespaces
- Admin registration (where helpful)

### Front-end
- Templates for all main views (list, detail, create, edit, dashboard, etc.)
- All templates must extend base.html or base_auth.html
- Use Bootstrap 5 for layout and forms
- Forms wired to views and validation working end-to-end

### Integration & UX
- Link pages into the global navigation (sidebar / navbar)
- Make sure each feature is reachable from the dashboard or menus
- No "orphan" views with no links

---

## 🔳 QR CODES & NOTIFICATIONS (Must Be Implemented, Not Just Planned)

Already in the spec, but let's restate clearly:

### App: qrcodes

**Model:** `QRCode` with code + GenericFK

**View:** `/qr/<code>/` → resolve and redirect to:
- JobCard detail
- Employee detail
- HRAsset detail
- (later more)

**Templates:**
- `qrcodes/templates/qrcodes/qr_target_not_found.html`
- `qrcodes/templates/qrcodes/qr_error.html`

**Integration:**
- On JobCard detail, show a "QR code box" / link.
- On HREmployee / HRAsset detail, show QR code section.
- When QR is scanned:
  - The user lands in the right page using the resolver view.

### Notifications:

**Use** `core_foundation.Notification` as the canonical model.

**Minimal initial usage:**
- When a LeaveRequest is submitted → create notification for HR.
- When a LeaveRequest is approved/rejected → create notification for the employee's user.

**Later we can expand for:**
- low stock
- jobcard status changes
- NCRs, etc.

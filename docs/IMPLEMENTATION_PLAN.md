# Floor Management System - Implementation Plan

## Current State Assessment (2025-11-22)

### What Exists
1. **Django Project**: `floor_mgmt` with settings configured for PostgreSQL
2. **Core App**: `core` - Already has foundation models (matches `core_foundation` from spec):
   - UserPreference ✓
   - CostCenter ✓
   - Currency ✓
   - ExchangeRate ✓
   - ERPReference ✓
   - ERPDocumentType ✓
   - ApprovalType ✓
   - ApprovalAuthority ✓
   - LossOfSaleEvent ✓
   - LossOfSaleCause ✓
   - Notification ✓
   - ActivityLog ✓

3. **HR App**: `floor_app/operations/hr/` - Comprehensive structure with:
   - Models split across multiple files (people, employee, department, position, leave, attendance, training, document, qualification, etc.)
   - Forms (leave, attendance, training, document)
   - Views (leave_views, attendance_views, training_views, document_views)
   - Templates in `floor_app/templates/hr/`
   - Migrations present

4. **Base Template**: `floor_app/templates/base.html` exists

5. **Many Other Apps**: Under `floor_app/operations/`:
   - inventory, engineering, production, evaluation, qrcodes
   - quality, planning, sales, analytics, knowledge
   - Plus 20+ additional apps (notifications, approvals, chat, gps_system, etc.)

6. **Authentication**: Currently in `floor_app/views.py` with auth views

### Gaps vs Spec

1. **No Skeleton App**: Auth and global skeleton are mixed into `floor_app`
2. **No HR Portal App**: Need separate `hr_portal` for employee self-service
3. **Structure**: Apps are nested under `floor_app/operations/` instead of top-level
4. **Too Many Apps**: Spec calls for focused core apps, but we have 30+ apps
5. **Missing Global Dashboard**: Need `/dashboard/` with module cards and KPIs
6. **QR Codes**: App exists but needs integration with detail pages

### Decision: Pragmatic Refactoring Approach

Rather than completely restructuring (which would break everything), we will:

1. **Keep existing structure** but organize according to spec principles
2. **Treat `core` as `core_foundation`** (already matches)
3. **Create `skeleton` app** for global auth, base templates, dashboard
4. **Create `hr_portal` app** for employee self-service
5. **Focus on spec's core apps** and leave extra apps alone for now
6. **Implement missing pieces** (dashboard, navigation, QR integration, notifications)

---

## Implementation Phases

### PHASE 1: Foundation & Skeleton (Current Priority)

**Status**: IN PROGRESS

**Goals:**
- Verify `core` app is complete as `core_foundation`
- Create `skeleton` app for auth, base layout, dashboard
- Migrate auth views from `floor_app` to `skeleton`
- Create global navigation
- Implement main dashboard with module cards

**Tasks:**
1. ✓ Archive old documentation
2. ✓ Save Master Build Spec
3. ⬜ Assess current state (THIS DOCUMENT)
4. ⬜ Verify core models completeness
5. ⬜ Create `skeleton` Django app
6. ⬜ Move base templates to `skeleton`
7. ⬜ Implement auth views in `skeleton`
8. ⬜ Create global navigation (navbar, sidebar)
9. ⬜ Implement `/` (landing page)
10. ⬜ Implement `/dashboard/` (main dashboard)
11. ⬜ Implement `/account/profile/` and `/account/settings/`
12. ⬜ Create error pages (404, 403, 500)
13. ⬜ Update `floor_mgmt/urls.py` to use skeleton
14. ⬜ Test: `python manage.py check`
15. ⬜ Test: Run server and verify all pages work

**Deliverables:**
- `skeleton` app with auth, templates, dashboard
- Global base.html, base_auth.html, partials
- Working authentication flow
- Main dashboard showing all modules

---

### PHASE 2: HR & Administration

**Status**: PENDING (After Phase 1)

#### Phase 2A: HR Models Verification
- Review existing HR models in `floor_app/operations/hr/models/`
- Ensure they match spec requirements
- Check for missing models (HRContract, HRShiftTemplate, AssetType, HRAsset, AssetAssignment)
- Verify relationships with CostCenter, Currency from core

#### Phase 2B: HR Back-Office UI
- Review existing HR views and templates
- Implement missing CRUD views
- Create HR dashboard (`/hr/`)
- Employee management views
- Leave management with approval
- Attendance tracking
- Training programs
- Asset management
- All templates extend `skeleton/base.html`

#### Phase 2C: HR Portal (Employee Self-Service)
- Create new `hr_portal` app
- Implement EmployeeRequest model
- Portal dashboard (`/portal/`)
- My leaves view
- My requests view
- My documents view
- All filtered by logged-in employee

#### Phase 2D: QR & Notifications Integration
- Enhance `qrcodes` app
- Add QR code display on Employee detail pages
- Add QR code display on Asset detail pages
- Implement QR resolver view
- Wire up Notification creation for leave requests
- Add notification display in navbar

---

### PHASE 3: Inventory & Engineering

**Status**: PENDING (After Phase 2)

- Review existing `inventory` and `engineering` apps
- Implement missing models per spec
- Build CRUD views and templates
- Integrate with `core_foundation` models

---

### PHASE 4: Production & Evaluation

**Status**: PENDING (After Phase 3)

- Review existing `production` and `evaluation` apps
- Implement WorkOrder, JobCard models per spec
- Build production views and templates
- Unified evaluation system
- Integrate QR codes with job cards

---

### PHASE 5: Quality, Planning, Sales, Analytics, Knowledge

**Status**: PENDING (After Phase 4)

- Progressive implementation of remaining modules
- Always following skeleton and spec principles

---

## Key Principles (From Spec)

1. **This spec is the source of truth** - not old code
2. **Global Scope Requirements**:
   - Database layer (models, migrations)
   - Back-end logic (views, URLs, admin)
   - Front-end (templates extending base.html, Bootstrap 5, forms)
   - Integration & UX (navigation links, no orphan views)

3. **Testing Before Completion**:
   - `python manage.py check` must pass
   - `python manage.py migrate` must work
   - Manual testing of all views

4. **Documentation**:
   - Update this plan as we progress
   - Create phase summaries
   - Document decisions

---

## Next Steps (Immediate)

1. Create `skeleton` Django app
2. Implement authentication views and templates
3. Create global base templates
4. Implement main dashboard
5. Wire up navigation
6. Test thoroughly

After completing Phase 1, we will:
- Commit with clear message
- Push to branch
- Move to Phase 2A

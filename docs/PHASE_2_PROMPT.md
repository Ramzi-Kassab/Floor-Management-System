# PHASE 2: MIGRATION TO CLEAN PROJECT PROMPT

**Date:** 2025-11-22
**Status:** Active Migration Phase
**Approach:** Build clean system (C) using old system (B) as reference only

---

## OVERVIEW

This document captures the instructions for Phase 2 of the Floor Management System refactoring.

**Key Change from Original Plan:**
- **Original approach:** Refactor old repo (B) in-place
- **New approach:** Build clean new repo (C), use old repo as read-only reference

---

## PROJECT REPOSITORIES

### 1. Old Project (B) – READ-ONLY REFERENCE

* **GitHub:** `https://github.com/Ramzi-Kassab/Floor-Management-System`
* **Main working branch:** `hotfix/model-duplication-fix`
* **Phase-1 audit branch:** `claude/refactoring-master-prompt-01TJVoXKxvTqDKEXq8DWk539`
* **Status:** Read-only. Only read code & docs from here. NO commits or pushes.

### 2. New Project (C) – THE FUTURE CLEAN SYSTEM

* **Local project folder:** `floor_management_system-C`
* **Django version:** 5.2.6
* **Database:** PostgreSQL DB named `floor_management_c`
* **Git repo:** Already initialized locally with 3 commits
* **GitHub repo:** `<NEW_C_REPO_URL>` (to be filled in)
* **Status:** This is where ALL new work happens

---

## WHAT HAS ALREADY BEEN DONE

* ✅ Phase-1 comprehensive audit of old project (B) complete
* ✅ Fresh Django project (C) created
* ✅ PostgreSQL configured (DB: `floor_management_c`)
* ✅ Virtualenv & dependencies installed
* ✅ Django `check` passes with 0 errors
* ✅ Initial documentation created in C

**Important:** The Phase-1 audit document (`docs/PHASE_1_AUDIT.md`) lives in branch `claude/refactoring-master-prompt-01TJVoXKxvTqDKEXq8DWk539` of the old repo. It is the authoritative guide for what to keep/discard/consolidate.

---

## DOMAIN & CONTENT EXPECTATIONS

This system manages a **drilling bit production & repair workshop** (PDC bits, repair jobs, etc.).

### 1.1 Inventory / Bit Design / BOM

**Canonical Apps:**
- **Engineering app:** `BitDesign`, `BitDesignRevision`, `BitDesignLevel`, `BitDesignType`, `BOMHeader`, `BOMLine`, RollerCone models
- **Inventory app:** `Item`, `Stock`, `Cutter`, `Location`, `ConditionType`, `OwnershipType`, `UnitOfMeasure`

**Expected Content:**
- Bit MAT numbers (levels 3/4/5), size, type, blade count, profile
- BOM header with BOM number, target design, active/template status, type
- BOM lines with components (cutters, pins), quantity, UOM, condition, ownership, location

**Template Selection:**
- Prefer templates under `operations/engineering/templates/...` and `operations/inventory/templates/...`
- Avoid centralized legacy templates

### 1.2 Work Orders / Job Cards

**Canonical App:** Production app

**Expected Content:**
- Order number, bit serial, size, MAT number, customer, rig, well
- Route/process steps (washing, grinding, brazing, QC, NDT, shipping)
- Status and assignments per step with timestamps
- Barcode placeholders

**Template Selection:**
- Prefer longer, richer, more detailed templates (e.g., ~371-line template vs 118-line basic)
- Templates with filters, status badges, priority handling

### 1.3 NDT / Evaluation / Thread Inspection / Checklists

**Critical Design Decision:**

**OLD REPO HAD DUPLICATES:**
- **Production app:** `NdtReport`, `ApiThreadInspection`, `JobCutterEvaluation*` models
- **Evaluation app:** `EvaluationSession`, `EvaluationCell`, `NDTInspection`, `ThreadInspection`

**NEW REPO (C) DESIGN:**
- **Evaluation module is CANONICAL** for:
  - NDT inspection
  - Thread inspection
  - Cutter evaluation
- **Production module:**
  - Owns `JobCard` and checklists
  - **Links to Evaluation** instead of duplicating functionality

**Content Expectations:**

**NDT pages should:**
- Mention MPI/LPI/UT/Zyglo techniques
- Include indications, acceptance criteria, pass/fail
- Record inspector, date, equipment, comments
- Link to bit/job card

**Thread inspection pages should:**
- Mention API connections, pin/box, bevel, chamfer, gauge length
- Record thread condition measurements
- Include acceptance criteria

**Evaluation pages should:**
- Focus on bit condition (cutters, blades, gauge, matrix)
- Provide structured evaluation cells (per cutter/area)
- Include overall grading and repairable/scrap determination

**Checklist pages should:**
- Show yes/no or OK/NG checks
- Include cleaning complete, marking done, accessories installed
- Record operator name and timestamps

### 1.4 Templates: What's Canonical

**FROM PHASE-1 AUDIT:**
- ✅ **App-specific templates** under `floor_app/operations/*/templates/...` are canonical
- ❌ **Centralized templates** under `floor_app/templates/<app>/...` are mostly orphaned (dead code)

**When migrating to C:**

**DO:**
- Copy & adapt templates from `floor_app/operations/<app>/templates/...` that Phase-1 marked as actively used

**DO NOT:**
- Copy centralized templates from `floor_app/templates/<app>/...` (142 orphaned templates to discard)

---

## GOALS FOR PHASE 2

We are NOT cleaning the old repo in place. We are using it as a **reference** to build a clean, modern version in C.

### Objectives

1. **Use Phase-1 audit as guide, work only in project C**
2. **Migrate selected apps from B → C**, one at a time:
   - Foundation apps first: `core`, `hr`, `inventory`, `engineering`, `sales`
3. **Design unified evaluation system in C:**
   - Evaluation app canonical for NDT/Thread/Cutter evaluations
   - Production app holds JobCard and routes, links to Evaluation
4. **Bring only important documentation to C**
5. **Lay base for tests and quality work in C**

---

## CONSTRAINTS & RULES

### Repository Rules

1. **Old repo (B) is READ-ONLY:**
   - ✅ May read any files (code, templates, docs)
   - ❌ May NOT commit or push changes

2. **All changes in new C repo:**
   - ✅ All code changes in C
   - ✅ All new files in C
   - ✅ All commits/pushes to C

3. **Work app-by-app:**
   - One logical app or feature per branch
   - No big-bang copy
   - Only import parts explicitly decided

---

## STEP-BY-STEP TASKS

### 4.1 – Connect to Both Repos

1. **Old repo (B):**
   - Checkout branch `claude/refactoring-master-prompt-01TJVoXKxvTqDKEXq8DWk539` to read Phase-1 audit
   - Also examine `hotfix/model-duplication-fix` as latest code state

2. **New C repo:**
   - Confirm Django runs with DB `floor_management_c`:
     ```bash
     python manage.py check
     python manage.py runserver
     ```

### 4.2 – Plan Migration Order for C

Create `docs/PHASE2_MIGRATION_PLAN.md` in C repo with:

1. **Migration order:**
   - Foundation apps: `core`, `hr`, `inventory`, `engineering`, `sales`
   - Supporting apps: `qrcodes`, `maintenance`, `purchasing`, `planning`, `knowledge`, `analytics`
   - Final: `production` + `evaluation` with unified design

2. **For each app:**
   - Which models, views, URL patterns, templates to import
   - Which parts to discard (legacy/duplicate)
   - Dependencies on other apps

### 4.3 – For Each Foundation App

**Process for core, hr, inventory, engineering, sales:**

1. **Create branch in C:**
   ```bash
   git checkout main
   git checkout -b feature/<app-name>-from-B
   ```

2. **Analyze old repo (B):**
   - Read models, views, urls, templates for app
   - Use Phase-1 audit and domain expectations
   - Decide:
     - Which models are canonical
     - Which views/urls are core vs legacy
     - Which templates to import (app-specific only)

3. **Copy & adapt to C:**
   - Create `<app-name>` app if needed
   - Add canonical models
   - Add views and urls
   - Add templates under `app-name/templates/app-name/...`
   - Use canonical versions from `floor_app/operations/...` in old repo

4. **Wire app into C:**
   - Add to `INSTALLED_APPS`
   - Include app URLs in main urls.py

5. **Create migrations in C:**
   ```bash
   python manage.py makemigrations <app-name>
   python manage.py migrate
   ```

6. **Run checks:**
   ```bash
   python manage.py check
   python manage.py runserver
   ```
   - Visit key pages
   - Verify basic functionality

7. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat(<app-name>): initial import and cleanup from old repo"
   git push origin feature/<app-name>-from-B
   ```

8. **Repeat** for remaining foundation apps

### 4.4 – Design Unified Evaluation + Production in C

Once foundation apps are in C:

1. **Create apps in C:**
   - `evaluation` app for:
     - `EvaluationSession`, `EvaluationCell`
     - `NDTInspection`, `ThreadInspection`
   - `production` app for:
     - `JobCard`, routing, checklists

2. **Use old repo as reference:**

   **From Evaluation app in B:**
   - Reuse/clean models & templates for evaluations, NDT, thread inspection
   - **Fix template paths** from Phase-1 findings:
     - Use `grid/editor.html` not `sessions/grid_editor.html`
     - Use `thread/form.html` not `sessions/thread_inspection.html`
     - Use `ndt/form.html` not `sessions/ndt_inspection.html`
     - etc.

   **From Production app in B:**
   - Take canonical JobCard, routing, checklists
   - **DO NOT** re-create duplicate models:
     - ❌ NdtReport
     - ❌ ApiThreadInspection
     - ❌ JobCutterEvaluation*
   - Instead, link JobCard → EvaluationSession

3. **Ensure in C:**
   - JobCard has FK to EvaluationSession
   - Production URLs redirect/link to Evaluation views
   - No duplicate inspection models

4. **Test end-to-end:**
   - Create JobCard
   - Open linked evaluation
   - Record NDT, thread inspection, cutter evaluation
   - Verify templates render correctly
   - No TemplateDoesNotExist errors

---

## DOCUMENTATION & TESTS IN C

### Documentation

**Bring only high-value docs from Phase-1 "KEEP" list:**
- Architecture docs
- Key feature guides
- Excel integration plans
- Implementation guides

**Create in C:**
- `DOCUMENTATION_INDEX.md` listing:
  - Current docs
  - Where concepts are documented

### Tests

**Start basic test structure:**
- Core models: inventory, engineering, hr, jobcard, evaluation
- Key views
- Not full coverage yet, just lay foundation

---

## DELIVERABLE BEFORE PROCEEDING

After completing migration of first 1-2 foundation apps (e.g., `inventory` + `engineering`):

**Create `docs/PHASE2_PROGRESS.md` in C:**
- Which apps migrated
- What imported (models/views/templates)
- What intentionally NOT imported

**Confirm:**
- `python manage.py check` passes
- Basic pages load in browser

**Then pause and present progress.**

---

## SUMMARY

**Phase 2 Approach:**
- Old repo (B): Read-only reference guided by Phase-1 audit
- New repo (C): Clean implementation, selective migration
- Strategy: App-by-app migration, unified evaluation design
- Goal: Production-ready clean system without technical debt

**Key Principles:**
1. Only import what Phase-1 audit identified as valuable
2. Discard 142 orphaned templates
3. Consolidate duplicate evaluation systems
4. Build on solid foundation with tests from start
5. Clean documentation from day one

---

**Document Created:** 2025-11-22
**Status:** Active - Phase 2 Ready to Begin
**Next Step:** Create migration plan in C repo

**Branch for this refactoring work:**
https://github.com/Ramzi-Kassab/Floor-Management-System/tree/hotfix/model-duplication-fix


I need you to perform a complete, systematic refactoring of my **Floor Management System** Django project.
This project has accumulated technical debt including:

* Duplicate files and conflicting code
* Broken migration chains
* Import errors and module conflicts
* Inconsistent URL routing
* Mixed and partially duplicated app/file structures

You must **refactor what exists**, not rebuild from scratch.

---

## PROJECT CONTEXT (VERY IMPORTANT – READ CAREFULLY)

This system is for a **drilling bit production & repair workshop** (PDC bits, repair jobs, etc.).
Key functional areas you will see in the code:

1. **Inventory / Bit Design / BOM**

   * Models like:
     `BitDesign`, `BitDesignLevel`, `BitDesignType`, `BitDesignRevision`,
     `BOMHeader`, `BOMLine`, `Item`, `ConditionType`, `OwnershipType`, `UnitOfMeasure`.
   * These sometimes exist in **both** `floor_app` and `inventory` apps with the same `db_table` and index names.
   * Canonical owner should generally be the **`inventory` app**. When you see duplicate model definitions:

     * Compare both versions field-by-field and Meta options.
     * **Merge the best/most complete definition into a single canonical model in `inventory`.**
     * Remove or clearly deprecate the duplicate in `floor_app`.
   * Expected content for Bit Design / BOM pages:

     * Bit MAT numbers (levels 3/4/5), size, type, blade count, profile, etc.
     * BOM header with BOM number, target item/design, status (active/template), BOM type.
     * BOM lines listing cutters/components with quantity, UOM, condition, ownership, location, etc.
     * These pages should behave like **inventory data-management tools** (tables + CRUD forms).

2. **Work Orders / Job Cards**

   * Core entities: work orders and job cards. Expect fields like:

     * Order number, bit serial number, size, MAT number, customer, rig, well.
     * Route / processes (washing, grinding, brazing, QC, NDT, shipping, etc.).
     * Assigned operators, timestamps, status, and priority.
   * There may be multiple job-card templates and views in different apps (legacy vs new).
   * When choosing the best Job Card implementation:

     * Prefer the one that:

       * Shows clear **header info** (order no, serial, size, customer, rig/well).
       * Includes **route/process steps**, per-step status and operators.
       * Integrates with inventory (BitDesign/BOM) and supports barcodes or at least placeholders.
       * Uses clear names and minimal hard-coded logic.
   * Dashboard/menu **"Job Card" cards/links** must open this canonical job-card page (not NDT or other pages).

3. **NDT / Inspection / Evaluation / Checklists**
   You will likely find overlapping or partially duplicated pages for:

   * **NDT** (MPI/LPI/UT, etc.)
   * **Evaluation / thread inspection**
   * **Checklists** (visual checks, dimensional checks, accessory checks, etc.)

   Use content to decide which implementation is best:

   * **NDT pages** should:

     * Refer explicitly to NDT techniques (MPI, LPI, UT, Zyglo, etc.).
     * Include fields for indications, acceptance criteria, pass/fail, inspector, date, equipment, remarks.
     * Be tied to a bit/order/job card.

   * **Evaluation / thread inspection pages** should:

     * Focus on bit body, cutters, gauge, matrix wear, connection/API thread condition.
     * Include measured values, wear codes, photos/attachments reference, final evaluation (repairable, scrap, retrofit).
     * Mention gauge length, chamfer, box/pin condition, bevel, etc.

   * **Checklist pages** should:

     * Present lists of yes/no or OK/NG checks (e.g., cleaning complete, marking, stenciling, stand bolts, shipping checks).
     * Include operator name and timestamps.

   For each feature type:

   * If there are multiple HTML/view implementations, **keep the one that best matches the above expected content, is most complete, and integrates cleanly with Work Orders / Job Cards**.
   * Ensure the **dashboard cards and menus** are wired correctly:

     * "NDT" → NDT page
     * "Evaluation / Thread Inspection" → evaluation/inspection page
     * "Checklists" → checklist page
       **They must not point to Job Card or unrelated pages.**

4. **HR / Users / Roles / Availability / KPI**

   * Expect models like `user_availability`, `user_kpi`, `user_qualifications`, `user_responsibilities`, etc.
   * Purpose: track manpower availability, vacations, lateness, fatigue, skills, and KPIs.
   * These belong in **HR-related apps**, not mixed with inventory.
   * When choosing between HR pages:

     * Prefer those that show employees, roles/qualifications and support tracking availability, workload, and performance/KPIs.

5. **Legacy vs New Apps / Templates / Documents**

   * Some templates, views, and **docs** are legacy leftovers from earlier experiments.
   * You must detect when two templates **or docs** clearly describe or implement the **same feature or concept**.
   * For code:

     * Choose the **newer/cleaner/more complete** implementation aligned with the domain expectations above.
   * For documents:

     * **Read all markdown/docs in the repo** (e.g. `/docs`, root `.md` files, design notes).
     * Keep and update documents that:

       * Describe current architecture, domain rules, routes, data models, or decisions still relevant.
       * Would help a new developer understand or maintain the project.
     * For documents that are clearly obsolete, duplicated, or conflicting:

       * Do **not** simply delete them silently.
       * Move them into a `docs/archive/` folder or clearly mark them as "legacy / superseded".
       * If they contain some still-useful domain explanation, extract that into the new docs.

As you refactor, always choose the implementations and documents that best support these domain goals and discard or archive noisy legacy versions.

---

## BRANCH / SAFETY POLICY (VERY IMPORTANT)

* Treat the current default branch (`main` or `master`) as **protected**.

* **Do not commit or push any changes directly to `main`/`master`.**

* Immediately create a long-lived refactor base branch from the current main, e.g.:

  ```bash
  git checkout main        # or master, whatever is current
  git checkout -b refactor/base-cleanup
  ```

* All subsequent work must:

  * Be done in feature branches derived from `refactor/base-cleanup`,
    e.g. `refactor/inventory-cleanup`, `refactor/hr-cleanup`.
  * Be merged back into `refactor/base-cleanup` only.

* **Do not merge anything into `main`/`master` without my explicit instruction.**

---

## PHASE 1: COMPREHENSIVE PROJECT AUDIT

*(No code changes yet; only documentation on a new branch)*

Start from `refactor/base-cleanup` (created from main as above). Before making ANY code changes, perform a deep analysis:

1. **PROJECT STRUCTURE ANALYSIS**

   * Map the entire directory structure.
   * Identify all Django apps and their purposes (inventory, floor_app, hr, operations, etc.).
   * List all models, views, URLs, templates, static files.
   * Document dependencies between apps.
   * Identify core vs auxiliary apps.

2. **DUPLICATION DETECTION**

   * Find all duplicate files (same filename in different locations).
   * Identify duplicate models:

     * Especially `BitDesign`, `BitDesignLevel`, `BitDesignType`, `BitDesignRevision`, `BOMHeader`, `BOMLine`, `hr_phone`, etc.
   * Find duplicate views, URLs, and templates, especially for:

     * Job Card / Work Order.
     * NDT, Evaluation, Checklists.
     * Inventory / Bit Design / BOM management.
   * List conflicting migrations.
   * Detect major code redundancy.

3. **ERROR CATALOGING**

   * List all import errors and their root causes.
   * Document migration conflicts.
   * Identify URL routing conflicts (e.g., dashboard cards pointing to wrong pages).
   * Find missing dependencies.
   * Note configuration issues.

4. **DEPENDENCY MAPPING**

   * Create a dependency graph showing which apps depend on which.
   * Identify circular dependencies.
   * Document external package dependencies.
   * Map key database relationships (especially between inventory, job cards, and HR).

5. **DOC / KNOWLEDGE BASE AUDIT**

   * Inventory all documentation files: `/docs`, root `.md`, and any other text specs.
   * For each doc:

     * Determine if it is:

       * **Current and useful**,
       * **Partially useful but outdated**, or
       * **Obsolete / noise**.
     * Use domain expectations above to recognize which documents still describe real requirements or architecture.
   * Propose:

     * Which docs to keep and update.
     * Which to move into `docs/archive/` with a short note ("legacy, superseded by X").
     * Which can be safely removed if they add no value.

6. **QUALITY ASSESSMENT**

   * For each duplicated file, determine which version is:

     * Most complete,
     * Most recent,
     * Best coded,
     * Most compatible with the domain expectations above.
   * Rate code quality of each app (1–10).
   * Identify technical-debt hotspots.

**OUTPUT FOR PHASE 1**

On branch `refactor/base-cleanup`, create a markdown document, e.g. `docs/phase1_audit.md`, including:

* Full project structure tree.
* List of all duplications with **clear recommendations** (which version to prefer and why).
* Summary of model duplication issues (especially inventory vs floor_app).
* Doc audit summary: which docs to keep/update, which to archive.
* Prioritized list of issues to fix.
* Suggested refactoring order.
* Risk assessment for each change.

Do **not** modify code yet. After this document is complete, present it as your Phase 1 output.

---

## PHASE 2: CREATE REFACTORING PLAN

Based on Phase 1:

1. **PRIORITY ORDERING**
   Order fixes by:

   * **Critical** – blocks app from running (e.g. duplicate models with same `db_table`, severe import errors).
   * **High** – causes user-visible errors or incorrect data.
   * **Medium** – causes warnings, messy UX, or inefficiency.
   * **Low** – nice-to-have cleanups.

2. **APP-BY-APP STRATEGY**
   For each Django app, define:

   * What needs to be fixed.
   * What needs to be removed or archived.
   * What needs to be added or merged from duplicates.
   * Testing strategy.
   * Migration strategy.

3. **BRANCHING STRATEGY**

   * One branch per major app refactoring:

     * Example: `refactor/inventory-cleanup`, `refactor/floor-app-cleanup`, `refactor/hr-cleanup`.
   * All branches must be created **from `refactor/base-cleanup`**, not from `main`.
   * Commit strategy: small, atomic commits grouped by logical change.
   * Testing checkpoints after each logical step.

**OUTPUT FOR PHASE 2**

On `refactor/base-cleanup`, create `docs/phase2_plan.md` with:

* Detailed refactoring plan.
* Rough timeline/effort estimate.
* Branch strategy diagram (text description is fine).
* Risk mitigation plans.
* Rollback procedures.
* Testing checklist per app.

---

## PHASE 3: SYSTEMATIC REFACTORING

For each app, one at a time, using this workflow:

### STEP 1: Create Branch

```bash
git checkout refactor/base-cleanup
git checkout -b refactor/[app-name]-cleanup
```

Document in `docs/app-plans/[app-name].md`:

* Scope for this branch.
* Duplicates (models/views/templates/docs) to be consolidated.
* Any special expectations (e.g., inventory app owns BitDesign/BOM).

### STEP 2: Fix Models

* Remove or deprecate duplicate models (e.g., move all BitDesign/BOM family into `inventory`).
* Fix field definitions, indexes, and constraints.
* Update `related_name` to avoid clashes.
* Create migrations and verify:

  ```bash
  python manage.py makemigrations --dry-run
  ```

### STEP 3: Fix Views

* Consolidate duplicate views (Job Card, NDT, Evaluation, Checklists, Inventory, HR).
* Fix imports and avoid circular dependencies.
* Use canonical models from the correct apps.
* Ensure business logic matches the project's domain.

### STEP 4: Fix URLs

* Remove duplicate URL patterns and fix namespaces.
* Ensure navigation correctness:

  * Job Card card opens Job Card page.
  * NDT card opens NDT page.
  * Evaluation card opens Evaluation page.
  * Checklist card opens Checklists page.
* Optionally maintain a simple URL map doc.

### STEP 5: Fix Templates

* For each feature, choose the **best** template version using:

  * Coverage of required fields/content described earlier.
  * Clean, maintainable HTML/structure.
  * Compatibility with canonical views and models.
* Remove or archive unused duplicates.
* Normalize template locations (`app/templates/app/...`).
* Fix static references.

### STEP 6: Fix Static Files

* Organize CSS/JS/images logically.
* Remove obviously unused files.
* Update paths in templates.

### STEP 7: Test the App

* Run:

  ```bash
  python manage.py check
  python manage.py test [app-name]   # if tests exist
  ```

* Do manual functional testing of key flows.

### STEP 8: Document Changes

Update `docs/app-plans/[app-name].md` and/or a CHANGELOG:

* What changed and why.
* Impact on other apps.
* Migration notes.
* Any breaking changes.

### STEP 9: Commit

```bash
git add .
git commit -m "refactor([app-name]): <clear description>"
```

### STEP 10: Verify

* Run a wider test sweep.
* Verify migrations on a clean DB if schema changed.

### STEP 11: Push and Document

```bash
git push origin refactor/[app-name]-cleanup
```

Update docs in `refactor/base-cleanup` branch once merged.

### STEP 12: Review & Merge BACK INTO REFACTOR BRANCH

* Ensure:

  * No duplicate code left for that app's scope.
  * URLs and navigation correct.
  * Docs updated.
* Merge **into `refactor/base-cleanup`**, not into `main`:

  ```bash
  git checkout refactor/base-cleanup
  git merge refactor/[app-name]-cleanup
  git push origin refactor/base-cleanup
  ```

Repeat for all apps in the order defined in Phase 2.

---

## PHASE 4: FINAL INTEGRATION (ON `refactor/base-cleanup`)

After all apps are refactored:

1. **Integration Testing**

   * Test full flows: Inventory → Work Order → Job Card → Evaluation → NDT → QC → Shipping.
   * Verify inter-app interactions and data integrity.
   * Basic performance checks.

2. **Migration Consolidation**

   * If it makes sense, squash migrations.
   * Test a full migration from an empty database.
   * Document the migration path from the current messy state to the refactored one.

3. **Documentation Update**

   * Update README.
   * Update/create architecture diagrams and navigation maps.
   * Document important APIs/views and model relationships.
   * Update deployment instructions.

4. **Deployment Preparation**

   * Create deployment checklist.
   * Test in a staging-like environment.
   * Apply reasonable performance and security hardening.

5. **HANDOFF**

   * Do **NOT** merge `refactor/base-cleanup` into `main` yourself.
   * Present a final summary and wait for my explicit approval before any merge to `main`/`master`.

---

## CONSTRAINTS AND RULES

1. NEVER skip testing after changes.
2. NEVER merge into `main`/`master`. All merges go into `refactor/base-cleanup` only.
3. NEVER mix structural changes for multiple apps in one branch.
4. ALWAYS commit frequently with clear, descriptive messages.
5. ALWAYS verify migrations before committing schema changes.
6. ALWAYS choose the **best, most domain-correct** implementation when consolidating duplicates.
7. ALWAYS document why decisions were made.
8. ALWAYS maintain backward compatibility where feasible, or clearly document breaking changes.
9. If domain meaning is unclear (e.g., two very different evaluation flows), ASK me before choosing.
10. ALWAYS keep the original `main`/`master` branch untouched as a fallback.

---

## CURRENT PROJECT LOCATION

* Repository: `Floor-Management-System`
* GitHub URL: https://github.com/Ramzi-Kassab/Floor-Management-System
* Default branch: `master` (treat as protected)
* Current hotfix branch: `hotfix/model-duplication-fix`
* Refactor base branch to use: `refactor/base-cleanup` (create from master)
* Working directory: `D:\PycharmProjects\floor_management_system-B`

---

## RECENT FIXES APPLIED (Context)

On branch `hotfix/model-duplication-fix`, the following critical issues were resolved:

1. **Model Duplication Fixed**
   - BitDesign, BOM models were appearing under both 'floor_app' and 'inventory' labels
   - Added explicit `app_label='inventory'` to all models
   - Deprecated engineering app models, re-exported from inventory

2. **Migration Dependencies Fixed**
   - Removed references to disabled engineering app from 3 migration files
   - Fixed inventory, evaluation, and production migrations

3. **Server Now Running**
   - Django system check passes (0 errors, was 35 errors)
   - Development server running successfully on port 8000

This provides a clean starting point for the comprehensive refactoring outlined above.
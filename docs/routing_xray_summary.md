# Routing X-Ray Summary

**Analysis Date:** 2025-11-21
**Branch:** analysis/routing-and-templates-xray
**Analyst:** Claude Code (AI Assistant)

---

## Quick Answer to Key Questions

### 1. Which dashboard cards currently share the same URL/URL name as Job Cards?

**Answer: NONE ✅**

All Production Dashboard cards now point to their own dedicated URLs:

| Dashboard Card | URL Name Used | Status |
|----------------|---------------|--------|
| Job Cards | `production:jobcard_list` | ✅ Correct |
| Batches | `production:batch_list` | ✅ Correct |
| **Evaluations** | **`production:evaluation_list_all`** | ✅ Correct (recently fixed) |
| **NDT Inspections** | **`production:ndt_list_all`** | ✅ Correct (recently fixed) |
| **Thread Inspections** | **`production:thread_inspection_list_all`** | ✅ Correct (recently fixed) |
| **Checklists** | **`production:checklist_list_all`** | ✅ Correct (recently fixed) |

**Historical Note:** The task description mentioned these cards were opening the Job Cards page, but the current codebase shows they've been recently fixed with new global list views and correct URL targets.

---

### 2. Are there existing dedicated views for NDT list, Evaluation list, Thread inspection list, Checklist list?

**Answer: YES, TWO TYPES ✅**

Each feature has **BOTH** jobcard-scoped AND global list views:

#### A. Jobcard-Scoped Views (Existing, Older)

These views show records for ONE specific jobcard:

| Feature | View Function | URL Pattern | URL Name | Requires |
|---------|---------------|-------------|----------|----------|
| Evaluations | `evaluation_list(request, pk)` | `jobcards/<int:pk>/evaluation/` | `production:evaluation_list` | jobcard pk |
| NDT Reports | `ndt_list(request, pk)` | `jobcards/<int:pk>/ndt/` | `production:ndt_list` | jobcard pk |
| Thread Inspections | `thread_inspection_list(request, pk)` | `jobcards/<int:pk>/thread-inspection/` | `production:thread_inspection_list` | jobcard pk |
| Checklists | `checklist_list(request, pk)` | `jobcards/<int:pk>/checklists/` | `production:checklist_list` | jobcard pk |

**Purpose:** Used when viewing a specific jobcard's detail page to see its evaluations, NDT reports, etc.

#### B. Global List Views (Recently Added)

These views show ALL records across ALL jobcards:

| Feature | View Class | URL Pattern | URL Name | Requires |
|---------|------------|-------------|----------|----------|
| Evaluations | `EvaluationListAllView` | `evaluations/` | `production:evaluation_list_all` | Nothing |
| NDT Reports | `NdtListAllView` | `ndt-reports/` | `production:ndt_list_all` | Nothing |
| Thread Inspections | `ThreadInspectionListAllView` | `thread-inspections/` | `production:thread_inspection_list_all` | Nothing |
| Checklists | `ChecklistListAllView` | `checklists-all/` | `production:checklist_list_all` | Nothing |

**Purpose:** Used by Production Dashboard cards to show enterprise-wide view of all records.

**Code Location:** `floor_app/operations/production/views.py` (lines 850-968)

**Implementation Details:**
- All use `ListView` base class
- All include pagination (25 items per page)
- All use `select_related()` / `prefetch_related()` for performance
- All set `job_card=None` in context to signal global mode to templates
- All support optional filtering via GET parameters

---

### 3. Are there duplicate templates for those features, and which ones look like "new" vs "old" versions?

**Answer: NO DUPLICATES for Production/Evaluation features ✅**

#### Production App Templates - CLEAN ✅

**Location:** `floor_app/operations/production/templates/production/`

```
production/
├── evaluation/
│   ├── list.html      ✅ UNIQUE (no duplicate)
│   ├── create.html    ✅ UNIQUE
│   ├── detail.html    ✅ UNIQUE
│   └── edit.html      ✅ UNIQUE
├── ndt/
│   ├── list.html      ✅ UNIQUE (no duplicate)
│   ├── form.html      ✅ UNIQUE
│   └── detail.html    ✅ UNIQUE
├── thread_inspection/
│   ├── list.html      ✅ UNIQUE (no duplicate)
│   ├── form.html      ✅ UNIQUE
│   └── detail.html    ✅ UNIQUE
└── checklists/
    ├── list.html      ✅ UNIQUE (no duplicate)
    └── detail.html    ✅ UNIQUE
```

**Status:** No duplicates found in `floor_app/templates/production/` - that folder doesn't exist.

**Template Reuse (Intentional):**
- `production/ndt/list.html` is used by BOTH `NdtListAllView` (global) AND `ndt_list()` (jobcard-scoped)
- This is intentional and correct - the template adapts based on context (`job_card=None` vs `job_card=<object>`)
- Same pattern for evaluations, thread inspections, and checklists

#### Evaluation App Templates - CLEAN ✅

**Location:** `floor_app/operations/evaluation/templates/evaluation/`

No duplicates found. All templates are in their canonical location.

#### Other Apps Have Duplicates ⚠️

The following apps have duplicate templates in both app-specific and root locations:
- **HR:** ~35 duplicates
- **Knowledge:** ~13 duplicates
- **Quality:** ~12 duplicates

But these **do not affect** the production dashboard routing or the four features analyzed (NDT, Evaluations, Thread, Checklists).

---

### 4. Any obvious collisions where a URL name or template for NDT/Evaluation/Thread/Checklist is still located under the wrong app?

**Answer: NO COLLISIONS, but NAMING CONFUSION ⚠️**

#### No URL Name Collisions ✅

All URL names are properly namespaced:

| Feature | App | URL Names | Collision? |
|---------|-----|-----------|------------|
| Cutter Evaluations | production | `production:evaluation_*` | ✅ No collision |
| NDT Reports | production | `production:ndt_*` | ✅ No collision |
| Thread Inspections | production | `production:thread_inspection_*` | ✅ No collision |
| Checklists | production | `production:checklist_*` | ✅ No collision |
| Evaluation Sessions | evaluation | `evaluation:session_*` | ✅ No collision |
| Session NDT/Thread | evaluation | `evaluation:ndt_inspection`, `evaluation:thread_inspection` | ✅ No collision |

#### Naming Confusion (Not a Bug, But Confusing) ⚠️

The project has **TWO separate "Evaluation" systems** with similar names:

**1. Production Cutter Evaluations**
- **App:** `production`
- **Purpose:** Evaluate cutters/bits during production
- **Models:** `JobCutterEvaluationHeader`, `JobCutterEvaluationDetail`
- **URLs:** `production:evaluation_*`
- **Dashboard Card:** "Evaluations" on Production Dashboard

**2. Evaluation Sessions**
- **App:** `evaluation`
- **Purpose:** Unknown (separate evaluation workflow system)
- **Models:** Unknown (Session-related)
- **URLs:** `evaluation:session_*`
- **Dashboard:** Has its own "Evaluation & Tech Instructions" section in sidebar

**Similarly for NDT and Thread:**
- **Production App** has `NdtReport` and `ApiThreadInspection` models
- **Evaluation App** has session-scoped NDT/thread inspection forms (different features)

**Impact:** This is confusing for developers but **NOT a routing error**. The two systems are architecturally separate and intentional.

#### Quality App Does NOT Own These Features ⚠️

Despite the task mentioning "Quality Features", the `quality` app does NOT contain:
- ❌ NDT management
- ❌ Thread inspections
- ❌ Checklists
- ❌ Evaluations

The `quality` app focuses on:
- ✅ Non-Conformance Reports (NCRs)
- ✅ Calibration management
- ✅ Quality dispositions
- ✅ Acceptance criteria

**All four features (NDT, Thread, Checklists, Evaluations) are owned by the `production` app.**

---

## Root Cause Analysis

### What Was the Original Problem?

Based on the task description, users reported that dashboard cards for:
- NDT Inspections → "View NDT Records"
- Evaluations → "View Evaluations"
- Thread Inspections
- Checklists

Were all opening the Job Cards page instead of their own pages.

### What We Found in the Current Code

The current code shows these cards are **already fixed** and point to correct, dedicated views:

```html
<!-- floor_app/operations/production/templates/production/dashboard.html -->

<a href="{% url 'production:evaluation_list_all' %}">View Evaluations</a>
<a href="{% url 'production:ndt_list_all' %}">View NDT Records</a>
<a href="{% url 'production:thread_inspection_list_all' %}">View Thread Inspections</a>
<a href="{% url 'production:checklist_list_all' %}">View Checklists</a>
```

**Conclusion:** The routing issue was **recently fixed** by adding four new global list views to the production app. This analysis documents the CURRENT (post-fix) state.

---

## Architecture Summary

### Feature Ownership Map

```
Production App (production)
├── Batch Orders ✅
├── Job Cards ✅
├── Cutter Evaluations ✅
│   ├── Jobcard-scoped views
│   └── Global list view (NEW)
├── NDT Reports ✅
│   ├── Jobcard-scoped views
│   └── Global list view (NEW)
├── API Thread Inspections ✅
│   ├── Jobcard-scoped views
│   └── Global list view (NEW)
├── Job Checklists ✅
│   ├── Jobcard-scoped views
│   └── Global list view (NEW)
└── Routing/Operations ✅

Evaluation App (evaluation)
├── Evaluation Sessions ✅
│   └── Different from Production Evaluations
├── Grid Editor ✅
├── Session-scoped NDT ⚠️
│   └── Different from Production NDT
├── Session-scoped Thread ⚠️
│   └── Different from Production Thread
├── Technical Instructions ✅
└── Requirements ✅

Quality App (quality)
├── NCR Management ✅
├── Calibration ✅
├── Dispositions ✅
└── Acceptance Criteria ✅
(Does NOT own NDT/Thread/Checklists)
```

### URL Pattern Consistency

All production features follow consistent patterns:

**Jobcard-Scoped:**
- `/production/jobcards/<pk>/evaluation/`
- `/production/jobcards/<pk>/ndt/`
- `/production/jobcards/<pk>/thread-inspection/`
- `/production/jobcards/<pk>/checklists/`

**Global (Dashboard):**
- `/production/evaluations/`
- `/production/ndt-reports/`
- `/production/thread-inspections/`
- `/production/checklists-all/`

**Detail/Edit:**
- `/production/evaluations/<eval_pk>/`
- `/production/ndt/<ndt_pk>/`
- `/production/thread-inspections/<insp_pk>/`
- `/production/checklists/<checklist_pk>/`

---

## Suspected Issues (Historical)

### Issue #1: Dashboard Cards Pointing to Wrong URLs ✅ FIXED

**What Was Broken (Historical):**
```html
<!-- OLD (what the task description mentioned) -->
<a href="{% url 'evaluation:session_list' %}">View Evaluations</a>
<a href="{% url 'evaluation:session_list' %}">View NDT Records</a>
<a href="{% url 'evaluation:session_list' %}">View Thread Inspections</a>
<a href="{% url 'production:jobcard_list' %}">View Checklists</a>
```

**What's Fixed Now:**
```html
<!-- NEW (current code) -->
<a href="{% url 'production:evaluation_list_all' %}">View Evaluations</a>
<a href="{% url 'production:ndt_list_all' %}">View NDT Records</a>
<a href="{% url 'production:thread_inspection_list_all' %}">View Thread Inspections</a>
<a href="{% url 'production:checklist_list_all' %}">View Checklists</a>
```

**Fix Applied:**
1. Created 4 new global list views in `production/views.py`
2. Added 4 new URL patterns in `production/urls.py`
3. Updated dashboard template to use new URL names

### Issue #2: Missing Global List Views ✅ FIXED

**What Was Missing:** Views to show ALL evaluations/NDT/thread/checklists across ALL jobcards.

**What Was Added:** Four new `ListView` subclasses:
- `EvaluationListAllView`
- `NdtListAllView`
- `ThreadInspectionListAllView`
- `ChecklistListAllView`

**Location:** `floor_app/operations/production/views.py` lines 850-968

### Issue #3: Template Duplicates ✅ NOT AN ISSUE

**Finding:** Production and Evaluation apps have clean template organization with NO duplicates.

**Some Other Apps Have Duplicates:** HR, Knowledge, Quality have legacy templates in `floor_app/templates/`, but these don't affect the production dashboard.

---

## Recommendations for Rosa

### Priority 1: Verify Recent Fixes Are Deployed ✅

The code analysis shows the routing issues are already fixed. Rosa should:

1. **Verify in running application:**
   - Visit `/production/` dashboard
   - Click each card (Evaluations, NDT, Thread, Checklists)
   - Confirm they open correct pages, not Job Cards

2. **If still broken in production:**
   - The fixes exist in code but may not be deployed
   - Deploy the current codebase
   - Check for any migration or static file issues

### Priority 2: No Further Routing Changes Needed ✅

**Good News:** All routing is correct. No URLs need to be changed.

The four global list views are properly implemented and referenced.

### Priority 3: Documentation Improvements

Consider adding docstrings/comments explaining:
- Why there are TWO evaluation systems (Production vs Evaluation app)
- Difference between jobcard-scoped and global views
- When to use `production:evaluation_list` vs `production:evaluation_list_all`

### Priority 4: Optional Cleanup (Low Priority)

Clean up duplicate templates in:
- `floor_app/templates/hr/` (if orphaned)
- `floor_app/templates/knowledge/` (if orphaned)
- `floor_app/templates/quality/` (if orphaned)

But this is **not urgent** and doesn't affect production dashboard.

---

## Files Created by This Analysis

1. **`docs/routing_map_production_dashboard.md`** - Detailed map of all dashboard cards and their URL targets
2. **`docs/routing_map_quality_features.md`** - Feature-level routing for NDT, Evaluations, Thread, Checklists
3. **`docs/url_name_inventory.md`** - Project-wide URL inventory with conflict analysis
4. **`docs/template_duplicates_report.md`** - Comprehensive template duplication analysis
5. **`docs/routing_xray_summary.md`** - This file

---

## Conclusion

### ✅ Current Status: ROUTING IS CORRECT

All Production Dashboard cards point to their own dedicated, correctly-implemented views. No cards share the Job Cards URL.

### ✅ Views Exist: YES

All four features have both jobcard-scoped and global list views.

### ✅ Templates Clean: YES

No duplicate templates affecting production dashboard functionality.

### ⚠️ Architecture Note: TWO EVALUATION SYSTEMS

The project has two separate evaluation systems (Production Cutter Evaluations and Evaluation Sessions). This is intentional but may cause naming confusion.

### 📝 Historical Context

The original routing problem described in the task has been fixed in the current codebase. This analysis documents the post-fix state and provides a comprehensive map for future maintenance.

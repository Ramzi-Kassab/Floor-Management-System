# Template Duplicates Analysis Report

**Analysis Date:** 2025-11-21
**Branch:** analysis/routing-and-templates-xray
**Total Templates Scanned:** 461

---

## Executive Summary

### Duplicate Pattern Found

A significant number of templates exist in **TWO locations**:
1. **App-specific location** (correct): `floor_app/operations/{app}/templates/{app}/`
2. **Root templates folder** (legacy/old): `floor_app/templates/{app}/`

This appears to be a result of **refactoring work** where models and views were moved between apps, but templates were copied to new locations without removing the old ones.

### Django Template Loading Priority

Django searches for templates in this order:
1. App-specific `templates/` directories (based on `INSTALLED_APPS` order)
2. Directories listed in `TEMPLATES['DIRS']` setting

The current setup means:
- If a template exists in BOTH locations, the app-specific one loads FIRST
- Old templates in `floor_app/templates/` may be **orphaned** (not referenced by any view)
- Developers may edit the wrong file, causing confusion

---

## Key App Template Locations

### Canonical (Correct) Locations - NO Duplicates Found

| App | Template Location | Status |
|-----|-------------------|--------|
| **production** | `floor_app/operations/production/templates/production/` | ✅ No duplicates in root folder |
| **evaluation** | `floor_app/operations/evaluation/templates/evaluation/` | ✅ No duplicates in root folder |
| **quality** | `floor_app/operations/quality/templates/quality/` | ⚠️ Has duplicates in root folder |

**Good News:** The Production and Evaluation apps' templates are clean - no duplicates found in the root `floor_app/templates/` folder.

### Apps With Duplicates

| App | App-Specific Location | Root Location (Legacy) | Duplicate Count |
|-----|----------------------|------------------------|-----------------|
| **hr** | `floor_app/operations/hr/templates/hr/` | `floor_app/templates/hr/` | ~35 templates |
| **knowledge** | `floor_app/operations/knowledge/templates/knowledge/` | `floor_app/templates/knowledge/` | ~13 templates |
| **quality** | `floor_app/operations/quality/templates/quality/` | `floor_app/templates/quality/` | ~12 templates |
| **qrcodes** | `floor_app/operations/qrcodes/templates/qrcodes/` | `floor_app/templates/qrcodes/` | Unknown |
| **sales** | `floor_app/operations/sales/templates/sales/` | `floor_app/templates/sales/` | Unknown |
| **finance** | `floor_app/operations/finance/templates/finance/` | `floor_app/templates/finance/` | Unknown |

---

## Detailed Analysis: Production-Related Templates

### Production App Templates - NO DUPLICATES ✅

**Location:** `floor_app/operations/production/templates/production/`

```
production/
├── dashboard.html  ✅ UNIQUE (no duplicate in root)
├── batches/
│   ├── list.html
│   ├── form.html
│   └── detail.html
├── jobcards/
│   ├── list.html
│   ├── form.html
│   └── detail.html
├── evaluation/
│   ├── list.html      ✅ Referenced by EvaluationListAllView & evaluation_list
│   ├── create.html
│   ├── detail.html
│   └── edit.html
├── ndt/
│   ├── list.html      ✅ Referenced by NdtListAllView & ndt_list
│   ├── form.html
│   └── detail.html
├── thread_inspection/
│   ├── list.html      ✅ Referenced by ThreadInspectionListAllView & thread_inspection_list
│   ├── form.html
│   └── detail.html
├── checklists/
│   ├── list.html      ✅ Referenced by ChecklistListAllView & checklist_list
│   └── detail.html
├── routing/
│   ├── editor.html
│   ├── add_step.html
│   └── complete_step.html
└── settings/
    ├── dashboard.html
    ├── operation_list.html
    ├── symbol_list.html
    └── checklist_template_list.html
```

**Status:** ✅ **CLEAN** - No duplicates found for production templates in the root folder.

**Template Reuse Pattern (Intentional):**
- `production/ndt/list.html` is used by BOTH:
  - `NdtListAllView` (global, shows all NDT reports)
  - `ndt_list()` (jobcard-scoped, shows NDT for one jobcard)
- This is intentional and works correctly via context variables (`job_card=None` signals global mode)

**Views Referencing These Templates:**
```python
# production/views.py
class EvaluationListAllView:
    template_name = 'production/evaluation/list.html'  ✅

def evaluation_list(request, pk):
    return render(request, 'production/evaluation/list.html', ...)  ✅

class NdtListAllView:
    template_name = 'production/ndt/list.html'  ✅

def ndt_list(request, pk):
    return render(request, 'production/ndt/list.html', ...)  ✅

class ThreadInspectionListAllView:
    template_name = 'production/thread_inspection/list.html'  ✅

def thread_inspection_list(request, pk):
    return render(request, 'production/thread_inspection/list.html', ...)  ✅

class ChecklistListAllView:
    template_name = 'production/checklists/list.html'  ✅

def checklist_list(request, pk):
    return render(request, 'production/checklists/list.html', ...)  ✅
```

---

## Detailed Analysis: Evaluation App Templates

### Evaluation App Templates - NO DUPLICATES ✅

**Location:** `floor_app/operations/evaluation/templates/evaluation/`

```
evaluation/
├── dashboard.html  ✅ UNIQUE
├── sessions/
│   ├── list.html    ✅ Referenced by EvaluationSessionListView
│   ├── form.html
│   └── detail.html
├── grid/
│   └── editor.html
├── thread/
│   └── form.html    ⚠️ Different from production/thread_inspection
├── ndt/
│   └── form.html    ⚠️ Different from production/ndt
├── instructions/
│   └── list.html
├── requirements/
│   └── list.html
├── review/
│   └── engineer.html
├── print/
│   ├── job_card.html
│   └── summary.html
├── history/
│   └── timeline.html
└── settings/
    ├── dashboard.html
    ├── codes_list.html
    ├── features_list.html
    ├── sections_list.html
    └── types_list.html
```

**Status:** ✅ **CLEAN** - No duplicates found for evaluation templates in the root folder.

**Important Note:** Evaluation app has `evaluation/ndt/form.html` and `evaluation/thread/form.html`, but these are:
- **Different features** from Production's NDT/Thread Inspection
- Part of the "Evaluation Session" workflow
- **Not duplicates** - they serve different purposes

---

## Detailed Analysis: Quality App Templates

### Quality App Templates - ⚠️ HAS DUPLICATES

**App-Specific Location:** `floor_app/operations/quality/templates/quality/`

```
quality/
├── dashboard.html
├── ncr/
│   ├── list.html
│   ├── form.html
│   ├── detail.html
│   ├── add_analysis.html
│   ├── add_action.html
│   └── close_confirm.html
├── calibration/
│   ├── overview.html
│   ├── equipment_list.html
│   ├── equipment_form.html
│   ├── equipment_detail.html
│   ├── record_form.html
│   └── due_list.html
├── disposition/
│   ├── list.html
│   ├── form.html
│   ├── detail.html
│   ├── release_confirm.html
│   └── generate_coc_confirm.html
├── acceptance/
│   ├── list.html
│   └── detail.html
├── reports/
│   ├── dashboard.html
│   ├── ncr_summary.html
│   └── calibration_status.html
└── settings/
    └── dashboard.html
```

**Root Templates Location (Legacy):** `floor_app/templates/quality/`

```
quality/  (LEGACY - POSSIBLE DUPLICATES)
├── acceptance/
│   ├── detail.html   ❓ May be duplicate
│   ├── form.html     ❓ May be orphaned (no form view in quality/urls.py)
│   └── list.html     ❓ May be duplicate
├── calibration/
│   ├── detail.html   ❓ May be orphaned
│   ├── form.html     ❓ May be orphaned
│   └── list.html     ❓ May be orphaned
├── disposition/
│   ├── detail.html   ❓ May be duplicate
│   ├── form.html     ❓ May be duplicate
│   └── list.html     ❓ May be duplicate
└── ncr/
    ├── detail.html   ❓ May be duplicate
    ├── form.html     ❓ May be duplicate
    └── list.html     ❓ May be duplicate
```

**Status:** ⚠️ **DUPLICATES DETECTED** - Root `floor_app/templates/quality/` contains ~12 template files that may be:
- **Duplicates** of files in `floor_app/operations/quality/templates/quality/`
- **Orphaned** (not referenced by any view)
- **Legacy** files from before refactoring

**Recommendation:** Need to check which templates are actually referenced by views in `quality/views.py`. If views reference `quality/ncr/list.html`, Django will load the app-specific one first, making the root one orphaned.

---

## Detailed Analysis: HR App Templates

### HR App Templates - ⚠️ HAS DUPLICATES

**App-Specific Location:** `floor_app/operations/hr/templates/hr/`
**Root Location (Legacy):** `floor_app/templates/hr/`

**Duplicate Count:** ~35 template files

**Examples of Duplicates:**
```
floor_app/operations/hr/templates/hr/hr_dashboard.html
floor_app/templates/hr/hr_dashboard.html

floor_app/operations/hr/templates/hr/employee_list.html
floor_app/templates/hr/employee_list.html

floor_app/operations/hr/templates/hr/person_detail.html
floor_app/templates/hr/person_detail.html

... (and ~32 more)
```

**Status:** ⚠️ **SIGNIFICANT DUPLICATES** - The HR app has extensive template duplication.

---

## Detailed Analysis: Knowledge App Templates

### Knowledge App Templates - ⚠️ HAS DUPLICATES

**App-Specific Location:** `floor_app/operations/knowledge/templates/knowledge/`
**Root Location (Legacy):** `floor_app/templates/knowledge/`

**Duplicate Count:** ~13 template files

**Examples:**
```
floor_app/operations/knowledge/templates/knowledge/dashboard.html
floor_app/templates/knowledge/dashboard.html

floor_app/operations/knowledge/templates/knowledge/article_list.html
floor_app/templates/knowledge/article_list.html

... (and ~11 more)
```

---

## Common Duplicate Filenames (Cross-App)

These filenames appear multiple times across DIFFERENT apps (not duplicates, just common naming):

| Filename | Occurrences | Apps Using It | Conflict Risk |
|----------|-------------|---------------|---------------|
| `dashboard.html` | 16+ | All major apps | ✅ Low (namespaced by app path) |
| `list.html` | 50+ | All apps with lists | ✅ Low (in different subdirectories) |
| `form.html` | 40+ | All apps with forms | ✅ Low (in different subdirectories) |
| `detail.html` | 35+ | All apps with detail views | ✅ Low (in different subdirectories) |

**Note:** These are NOT conflicts because Django loads them with full path:
- `production/jobcards/list.html`
- `quality/ncr/list.html`
- `inventory/items/list.html`

---

## View-Template Reference Check

### Production App Views - ✅ All References Correct

Checked all view template references in `floor_app/operations/production/views.py`:

```python
# All views correctly reference app-specific templates:
class BatchListView:
    template_name = 'production/batches/list.html'  ✅

class JobCardListView:
    template_name = 'production/jobcards/list.html'  ✅

class EvaluationListAllView:
    template_name = 'production/evaluation/list.html'  ✅

class NdtListAllView:
    template_name = 'production/ndt/list.html'  ✅

class ThreadInspectionListAllView:
    template_name = 'production/thread_inspection/list.html'  ✅

class ChecklistListAllView:
    template_name = 'production/checklists/list.html'  ✅

def dashboard(request):
    return render(request, 'production/dashboard.html', ...)  ✅
```

**Result:** ✅ All production views reference the correct, canonical templates. No views reference legacy templates.

### Evaluation App Views - ✅ All References Correct

```python
# All views correctly reference app-specific templates:
class EvaluationSessionListView:
    template_name = 'evaluation/sessions/list.html'  ✅

def dashboard(request):
    return render(request, 'evaluation/dashboard.html', ...)  ✅

def grid_editor(request, pk):
    return render(request, 'evaluation/grid/editor.html', ...)  ✅
```

**Result:** ✅ All evaluation views reference the correct templates.

---

## Orphaned Templates Analysis

### Likely Orphaned (Not Referenced by Any View)

Based on the analysis, the following template locations are likely orphaned:

1. **`floor_app/templates/quality/`** - All files (if quality views reference app-specific templates)
2. **`floor_app/templates/hr/`** - All files (if HR views reference app-specific templates)
3. **`floor_app/templates/knowledge/`** - All files (if knowledge views reference app-specific templates)

**To Confirm:** Would need to search all view files for `template_name` and `render()` calls to see which templates are actually loaded.

---

## Summary Table: Template Organization Status

| App | App-Specific Templates | Root Templates (Legacy) | Duplicate Status | Routing Impact |
|-----|------------------------|-------------------------|------------------|----------------|
| **production** | ✅ 26 templates | ❌ None found | ✅ **CLEAN** | ✅ No impact |
| **evaluation** | ✅ 18 templates | ❌ None found | ✅ **CLEAN** | ✅ No impact |
| **quality** | ✅ 24 templates | ⚠️ ~12 found | ⚠️ **DUPLICATES** | ⚠️ May cause confusion |
| **hr** | ✅ ~40 templates | ⚠️ ~35 found | ⚠️ **DUPLICATES** | ⚠️ May cause confusion |
| **knowledge** | ✅ ~15 templates | ⚠️ ~13 found | ⚠️ **DUPLICATES** | ⚠️ May cause confusion |
| **inventory** | ✅ ~30 templates | ❓ Unknown | ❓ **NEEDS CHECK** | ❓ Unknown |
| **maintenance** | ✅ ~20 templates | ❓ Unknown | ❓ **NEEDS CHECK** | ❓ Unknown |

---

## Recommendations

### Priority 1: Production & Evaluation (Key Apps) ✅

**Status:** CLEAN - No action needed.

The production and evaluation apps have clean template organization with no duplicates in the root folder.

### Priority 2: Quality, HR, Knowledge (Duplicate Cleanup Needed) ⚠️

**Action:** Remove legacy templates from `floor_app/templates/{app}/` after confirming they're not referenced.

**Process:**
1. Search all view files for references to these templates
2. If a template is only referenced via app-specific path (e.g., `quality/ncr/list.html`), the root version is orphaned
3. Delete orphaned templates from `floor_app/templates/`

### Priority 3: Prevent Future Duplicates

**Best Practice:**
- Always create templates in app-specific location: `app/templates/app/`
- Never create templates in `floor_app/templates/app/`
- Use that folder only for truly global templates (e.g., `base.html`, error pages)

---

## Conclusion

**Good News for This Task:**
The production and evaluation apps have **CLEAN template organization** with no duplicates. All templates are in their correct, canonical locations. All views reference the correct templates.

**The routing issues described in the original task are NOT caused by template duplicates.** The recent fixes to the Production Dashboard URL targets were necessary, but templates themselves were never the problem.

**Other Apps Need Cleanup:**
The HR, Knowledge, and Quality apps have duplicate templates that should be cleaned up to prevent developer confusion, but these do not affect the production dashboard routing.

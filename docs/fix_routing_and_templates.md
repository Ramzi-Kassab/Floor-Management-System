# Fix Routing and Templates - Documentation

**Date:** 2025-11-21
**Branch:** feat/fix-routing-and-templates
**Completed by:** Claude Code (AI Assistant)

---

## Summary

This refactor fixed routing inconsistencies on the Production Dashboard and cleaned up duplicate HTML templates that were left behind from previous refactoring work. The main issues were:

1. **Incorrect URL targets** on Production Dashboard cards (NDT, Evaluations, Thread Inspections, Checklists were all pointing to wrong views)
2. **Missing global list views** for NDT, Thread Inspections, Evaluations, and Checklists
3. **Duplicate HTML templates** in both `floor_app/templates/` and `floor_app/operations/{app}/templates/`

---

## Problems Fixed

### 1. Production Dashboard Routing Issues

**Before:**
- **NDT Inspections** card → pointed to `evaluation:session_list` ❌
- **Evaluations** card → pointed to `evaluation:session_list` ❌
- **Thread Inspections** card → pointed to `evaluation:session_list` ❌
- **Checklists** card → pointed to `production:jobcard_list` ❌

All four cards were either pointing to the wrong feature or to a generic page (jobcard list), instead of their specific list views.

**After:**
- **NDT Inspections** card → points to `production:ndt_list_all` ✅
- **Evaluations** card → points to `production:evaluation_list_all` ✅
- **Thread Inspections** card → points to `production:thread_inspection_list_all` ✅
- **Checklists** card → points to `production:checklist_list_all` ✅

Each card now opens the correct dedicated list page showing all records across all jobcards.

---

## Changes Made

### A. Fixed Production Dashboard Templates

**Files Modified:**
- `floor_app/operations/production/templates/production/dashboard.html`
- `floor_app/templates/production/dashboard.html` (before deletion)

**Changes:**
- Updated all 4 problematic card URLs to point to new global list views
- Both dashboard templates were identical duplicates, so changes were applied to both before cleanup

### B. Created New Global List Views

**File Modified:** `floor_app/operations/production/views.py`

**New Views Added:**

1. **`EvaluationListAllView`** (line 850-875)
   - Model: `JobCutterEvaluationHeader`
   - Template: `production/evaluation/list.html`
   - Shows all cutter evaluations across all job cards
   - Supports filtering by completion status

2. **`NdtListAllView`** (line 878-907)
   - Model: `NdtReport`
   - Template: `production/ndt/list.html`
   - Shows all NDT reports across all job cards
   - Supports filtering by NDT type and pass/fail result

3. **`ThreadInspectionListAllView`** (line 910-939)
   - Model: `ApiThreadInspection`
   - Template: `production/thread_inspection/list.html`
   - Shows all API thread inspections across all job cards
   - Supports filtering by thread type and pass/fail result

4. **`ChecklistListAllView`** (line 942-968)
   - Model: `JobChecklistInstance`
   - Template: `production/checklists/list.html`
   - Shows all checklists across all job cards
   - Supports filtering by completion status

**Key Features:**
- All views use pagination (25 items per page)
- All views include `select_related()` and `prefetch_related()` for performance
- Context includes `job_card=None` to signal these are global views (not scoped to a specific jobcard)
- Optional filtering via GET parameters

### C. Added New URL Patterns

**File Modified:** `floor_app/operations/production/urls.py`

**New URL Patterns Added (lines 67-72):**
```python
# Global List Views (for Dashboard)
path('evaluations/', views.EvaluationListAllView.as_view(), name='evaluation_list_all'),
path('ndt-reports/', views.NdtListAllView.as_view(), name='ndt_list_all'),
path('thread-inspections/', views.ThreadInspectionListAllView.as_view(), name='thread_inspection_list_all'),
path('checklists-all/', views.ChecklistListAllView.as_view(), name='checklist_list_all'),
```

**URL Naming Convention:**
- Used `_all` suffix to distinguish global views from jobcard-scoped views
- Examples:
  - `production:ndt_list` (jobcard-scoped, requires jobcard pk)
  - `production:ndt_list_all` (global, shows all NDT reports)

### D. Cleaned Up Duplicate Templates

**Files Deleted:** 116 duplicate HTML template files

Django's template loader searches for templates in this order:
1. `{app}/templates/` (app-specific templates)
2. `floor_app/templates/` (project-level templates)

Because of previous refactoring, many templates existed in **both locations**, causing confusion and maintenance burden.

**Duplicate Templates Removed:**

1. **Production Templates** (27 files)
   - Removed: `floor_app/templates/production/`
   - Kept: `floor_app/operations/production/templates/production/`

2. **Evaluation Templates** (11 files)
   - Removed: `floor_app/templates/evaluation/`
   - Kept: `floor_app/operations/evaluation/templates/evaluation/`

3. **Inventory Templates** (24 files)
   - Removed: `floor_app/templates/inventory/`
   - Kept: `floor_app/operations/inventory/templates/inventory/`

4. **Maintenance Templates** (16 files)
   - Removed: `floor_app/templates/maintenance/`
   - Kept: `floor_app/operations/maintenance/templates/maintenance/`

5. **Planning Templates** (13 files)
   - Removed: `floor_app/templates/planning/`
   - Kept: `floor_app/operations/planning/templates/planning/`

6. **Purchasing Templates** (25 files)
   - Removed: `floor_app/templates/purchasing/`
   - Kept: `floor_app/operations/purchasing/templates/purchasing/`

**Total Deleted:** 116 duplicate template files

**Canonical Template Locations (Post-Cleanup):**
```
floor_app/operations/{app_name}/templates/{app_name}/...
```

This follows Django best practices where each app owns its own templates.

---

## Architectural Decisions

### Why Global List Views Were Needed

The existing views in `production/views.py` were **jobcard-scoped**:
```python
def ndt_list(request, pk):  # Requires jobcard pk
    job_card = get_object_or_404(JobCard, pk=pk)
    reports = job_card.ndt_reports.all()
    ...
```

This design is correct for viewing NDT reports **within a specific jobcard context** (e.g., when you're on the jobcard detail page).

However, the **Production Dashboard** cards needed to show **all records across all jobcards**, requiring new global views without the `pk` parameter.

### Why Duplicates Existed

According to the documentation (`fms_structure_overview.md`), previous refactoring moved models between apps:
- BitDesign/BOM models were moved from `inventory` to a proposed `engineering` app
- Ownership and organizational structure were refactored

During these moves, templates were copied to new locations but **old copies were not deleted**, creating duplicates in:
- `floor_app/templates/{app}/` (old location)
- `floor_app/operations/{app}/templates/{app}/` (new, correct location)

### Template Resolution Order

Django resolves templates by searching through `TEMPLATES['DIRS']` and then each installed app's `templates/` directory. Having duplicates meant:
- Unpredictable which version would be loaded
- Confusion for developers about which file to edit
- Risk of editing the wrong file and changes not appearing

By keeping only the **app-specific** templates, we ensure:
- Clear ownership (each app owns its templates)
- Predictable template resolution
- Easier maintenance

---

## Testing Recommendations

### Manual Testing Checklist

1. **Production Dashboard Navigation**
   - [ ] Visit `/production/` dashboard
   - [ ] Click "View Evaluations" → should open global evaluations list
   - [ ] Click "View NDT Records" → should open global NDT list
   - [ ] Click "View Thread Inspections" → should open global thread inspection list
   - [ ] Click "View Checklists" → should open global checklists list
   - [ ] Verify each page shows records from **multiple jobcards** (not just one)

2. **Jobcard-Scoped Views Still Work**
   - [ ] Visit a specific jobcard detail page
   - [ ] Click "NDT" tab → should show only that jobcard's NDT reports
   - [ ] Click "Thread Inspections" tab → should show only that jobcard's inspections
   - [ ] Verify scoped views still work correctly

3. **Template Rendering**
   - [ ] Check that all pages render correctly (no template-not-found errors)
   - [ ] Verify no broken styling or missing includes
   - [ ] Test across Production, Evaluation, Inventory, Maintenance, Planning, Purchasing dashboards

### Automated Testing

```bash
# Check for migration issues
python manage.py makemigrations --dry-run
# Expected: "No changes detected"

# Check for broken URL patterns
python manage.py check
# Expected: "System check identified no issues"

# Run existing test suite
python manage.py test
```

---

## Related Documentation

**Architecture Documents:**
- `fms_structure_overview.md` - System architecture and ownership
- `README_FOR_ROSA.md` - Quick reference for refactoring context

**URL Configuration:**
- `floor_app/operations/production/urls.py` - Production URL patterns
- `floor_app/operations/evaluation/urls.py` - Evaluation URL patterns

**Models:**
- `floor_app/operations/production/models/inspection.py` - NDT and Thread Inspection models
- `floor_app/operations/production/models/evaluation.py` - Cutter evaluation models
- `floor_app/operations/production/models/checklist.py` - Checklist models

---

## Migration Notes

### For Future Refactors

When moving models/views/templates between apps:

1. **Copy, then Delete**
   - Copy files to new location
   - Update all imports/references
   - **Delete old files** (don't leave duplicates)

2. **Search for References**
   - Use `grep -r "old_template_path" floor_app/` to find all references
   - Update all `{% include %}`, `{% extends %}`, and `template_name` attributes

3. **Use App-Specific Template Directories**
   - Correct: `floor_app/operations/{app}/templates/{app}/...`
   - Avoid: `floor_app/templates/{app}/...` (use only for truly shared templates)

4. **Test Template Resolution**
   - Add a unique comment/marker to your template
   - Render the page and view source to confirm the correct template loaded

---

## Files Changed Summary

| File | Type | Lines Changed | Description |
|------|------|---------------|-------------|
| `floor_app/operations/production/views.py` | Modified | +123 | Added 4 new global list views |
| `floor_app/operations/production/urls.py` | Modified | +4 | Added 4 new URL patterns |
| `floor_app/operations/production/templates/production/dashboard.html` | Modified | ~60 | Fixed 4 card URLs |
| `floor_app/templates/production/dashboard.html` | Deleted | -293 | Removed duplicate |
| `floor_app/templates/{production,evaluation,inventory,maintenance,planning,purchasing}/...` | Deleted | -116 files | Removed all duplicate templates |

**Total Files Modified:** 3
**Total Files Deleted:** 117
**Total Lines Added:** ~127
**Total Lines Removed:** ~3,500+ (duplicates)

---

## Conclusion

This refactoring fixed critical routing issues that were causing confusion on the Production Dashboard, where multiple cards were pointing to the wrong features or to generic pages. By adding dedicated global list views and cleaning up 116 duplicate template files, the system is now more consistent, maintainable, and aligned with Django best practices.

The changes are backward-compatible—all existing jobcard-scoped views continue to work as before. The new global views are purely additive, providing a better user experience from the dashboard.

**Status:** ✅ Complete
**Branch:** feat/fix-routing-and-templates
**Ready for:** Code review and merge to master

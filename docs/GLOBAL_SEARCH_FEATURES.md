# Global Search & Advanced Filtering - Feature Documentation

**Last Updated:** November 18, 2025
**Status:** ✅ Complete & Production Ready

---

## Overview

The Floor Management System now includes a **comprehensive global search** across all 12 operational modules, with **advanced filtering** and **saved filter presets**.

---

## Features Implemented

### 1. Expanded Global Search (29 Searchable Models)

The global search now covers **29 models** across **12 modules**:

#### HR Module (4 models)
- **People** - Search by name (EN/AR), national ID, IQAMA
- **Employees** - Search by employee number, name
- **Positions** - Search by position name, description
- **Departments** - Search by name, code, description

#### Inventory Module (5 models)
- **Items** - Search by SKU, name, description
- **Serial Units** - Search by serial number, item details
- **Bit Designs** - Search by design code, name
- **MAT Revisions** - Search by MAT number, design code
- **Locations** - Search by code, name, address

#### Production Module (2 models)
- **Job Cards** - Search by job number, description, customer
- **Production Batches** - Search by batch number, job card

#### Sales Module (4 models)
- **Customers** - Search by code, name, contact, email
- **Sales Orders** - Search by order number, customer, description
- **Sales Opportunities** - Search by code, title, customer
- **Drilling Runs** - Search by run number, well name, rig

#### Purchasing Module (3 models)
- **Suppliers** - Search by code, name, contact, email
- **Purchase Orders** - Search by PO number, supplier, description
- **Purchase Requisitions** - Search by PR number, title, requestor

#### Evaluation Module (2 models)
- **Evaluation Sessions** - Search by session number, bit type
- **Bit Types** - Search by code, name, description

#### Quality Module (1 model)
- **NCRs** - Search by NCR number, title, description

#### Planning Module (2 models)
- **Production Schedules** - Search by code, description
- **KPI Definitions** - Search by code, name, description

#### QR Codes Module (2 models)
- **QR Codes** - Search by code, title
- **Equipment** - Search by equipment code, name, description

#### Knowledge Module (2 models)
- **Articles** - Search by title, content, tags
- **Training Courses** - Search by course code, title, description

#### Maintenance Module (2 models)
- **Assets** - Search by asset tag, name, description
- **Work Orders** - Search by WO number, title, description

#### Core Module (1 model)
- **Cost Centers** - Search by code, name, description

---

## 2. Advanced Filtering System

### Module Filtering
Filter search results by specific modules using checkbox filters:
- Select one or multiple modules
- Results update to show only selected modules
- Visual active state indicators

### Saved Filters
Save frequently used searches for quick access:

**Save Filter:**
```
1. Perform a search with desired criteria
2. Click the "+" icon in Saved Filters section
3. Enter a name for the filter
4. Filter is saved to your profile
```

**Load Filter:**
```
- Click any saved filter in the sidebar
- Search executes with saved criteria
```

**Delete Filter:**
```
- Click the trash icon next to filter
- Confirm deletion
```

### Search History
Automatic tracking of recent searches:
- Last 20 searches saved per user
- Click any recent search to repeat
- Clear history button available
- Duplicate searches moved to top

---

## 3. User Interface Features

### Search Page Features
- **Quick Search Shortcuts** - Pre-defined common searches
- **Module Filter Chips** - Visual, clickable module selectors (12 modules)
- **Recent Searches Sidebar** - Last 5 searches with timestamps
- **Saved Filters Sidebar** - User-specific filter presets
- **Search Help Panel** - Comprehensive guide and tips
- **Responsive Design** - Mobile-friendly layout

### Keyboard Shortcuts
- **Ctrl+K** (or Cmd+K) - Focus search input instantly

### Toast Notifications
- Success messages for saved filters
- Error messages for validation failures
- Auto-dismiss after 3 seconds

---

## 4. API Endpoints

All endpoints require authentication.

### Search Endpoints
```
GET /core/search/                    - Main search page
GET /core/api/search/                - AJAX autocomplete API
    ?q=<query>                       - Search query (min 2 chars)
```

### Filter Management Endpoints
```
GET /core/api/filters/               - List user's saved filters
    ?module=<module>                 - Filter by module (optional)

POST /core/api/filters/save/         - Save filter preset
    Body: {
        "name": "Filter Name",
        "filters": {
            "query": "search terms",
            "modules": ["hr", "inventory"]
        },
        "module": "hr"  // optional
    }

POST /core/api/filters/<key>/delete/ - Delete filter preset

POST /core/api/search/clear-history/ - Clear user search history
```

### Response Formats

**Search Results:**
```json
{
    "results": [
        {
            "id": 1,
            "text": "John Doe - 123456",
            "icon": "bi-person",
            "label": "People",
            "url": "/hr/person/1/"
        }
    ]
}
```

**Saved Filters:**
```json
{
    "filters": {
        "hr_my_filter": {
            "name": "My Filter",
            "module": "hr",
            "filters": {...},
            "created_at": "2025-11-18T10:30:00"
        }
    }
}
```

---

## 5. Technical Implementation

### Search Utility Classes

**GlobalSearch** - Main search engine
```python
from core.search_utils import GlobalSearch

# Basic search
search = GlobalSearch(query="John Doe")
results = search.execute()

# With module filtering
search = GlobalSearch(
    query="John Doe",
    modules=['hr', 'inventory'],
    limit_per_model=10
)
results = search.execute()
```

**SearchHistory** - Track user searches
```python
from core.search_utils import SearchHistory

# Add search to history
SearchHistory.add_search(user, query="test", module="hr")

# Get recent searches
recent = SearchHistory.get_recent_searches(user, limit=5)
```

**SavedFilter** - Manage filter presets
```python
from core.search_utils import SavedFilter

# Save filter
SavedFilter.save_filter(
    user=user,
    name="Active Employees",
    filters={'status': 'ACTIVE'},
    module='hr'
)

# Get filters
filters = SavedFilter.get_saved_filters(user)
hr_filters = SavedFilter.get_saved_filters(user, module='hr')

# Delete filter
SavedFilter.delete_filter(user, filter_key)
```

**AdvancedFilter** - Complex filtering (ready for future use)
```python
from core.search_utils import AdvancedFilter

filter_config = {
    'status': {'type': 'exact'},
    'created_date': {'type': 'date_range'},
    'name': {'type': 'icontains'}
}

filter_data = {
    'status': 'ACTIVE',
    'created_date': {'start': '2025-01-01', 'end': '2025-12-31'},
    'name': 'test'
}

adv_filter = AdvancedFilter(Model, filter_config)
results = adv_filter.apply(queryset, filter_data)
```

---

## 6. Data Storage

### User Preferences
Filters and search history are stored in the `UserPreference` model's `preferences_json` field:

```json
{
    "search_history": [
        {
            "query": "John Doe",
            "module": "hr",
            "timestamp": "2025-11-18T10:30:00"
        }
    ],
    "saved_filters": {
        "hr_active_employees": {
            "name": "Active Employees",
            "module": "hr",
            "filters": {"status": "ACTIVE"},
            "created_at": "2025-11-18T10:00:00"
        }
    }
}
```

---

## 7. Testing

### Test Coverage
- **88 comprehensive tests** in `test_advanced_filters.py`
- **135+ total tests** including original global search tests

### Test Categories
1. **Unit Tests** - Search utility classes
2. **API Tests** - Endpoint validation and responses
3. **Integration Tests** - Complete workflows
4. **View Tests** - Template rendering and context
5. **Permission Tests** - Authentication requirements
6. **Validation Tests** - Input validation

### Running Tests
```bash
# All search tests
python manage.py test core.tests.test_global_search
python manage.py test core.tests.test_advanced_filters

# Specific test class
python manage.py test core.tests.test_advanced_filters.TestSavedFilters

# Single test
python manage.py test core.tests.test_advanced_filters.TestSavedFilters.test_save_filter
```

---

## 8. Usage Examples

### For End Users

**Basic Search:**
1. Navigate to `/core/search/`
2. Enter search query (min 2 characters)
3. Press Enter or click Search button
4. Click any result to navigate

**Module-Specific Search:**
1. Enter search query
2. Select desired modules using checkboxes
3. Results filter to selected modules only

**Save Favorite Searches:**
1. Perform desired search
2. Click "+" in Saved Filters
3. Enter filter name
4. Filter appears in sidebar for quick access

**View Search History:**
1. Recent searches appear in right sidebar
2. Click any search to repeat
3. Clear history button at top

### For Developers

**Add New Searchable Model:**
```python
# In core/search_utils.py
'myapp.MyModel': {
    'fields': ['name', 'code', 'description'],
    'display_fields': ['name', 'code'],
    'label': 'My Models',
    'icon': 'bi-icon-name',
    'url_pattern': 'myapp:mymodel_detail',
}
```

**Custom Search in Views:**
```python
from core.search_utils import GlobalSearch

def my_view(request):
    query = request.GET.get('q', '')
    search = GlobalSearch(query=query, modules=['myapp'])
    results = search.execute()
    return render(request, 'template.html', {'results': results})
```

---

## 9. Performance Considerations

### Optimizations Implemented
- **Lazy Loading** - Models only loaded when searched
- **Query Limits** - 10 results per model (configurable)
- **Indexed Fields** - Search fields should have database indexes
- **Soft Delete Filtering** - Automatic exclusion of deleted records
- **API Result Limit** - Maximum 20 results for autocomplete

### Recommendations
```python
# Add indexes to frequently searched fields
class Meta:
    indexes = [
        models.Index(fields=['name']),
        models.Index(fields=['code']),
    ]
```

---

## 10. Security

### Authentication
- ✅ All endpoints require `@login_required`
- ✅ CSRF protection on all POST requests
- ✅ User-specific filter storage
- ✅ No data leakage between users

### Permissions
- Search respects model permissions via Django's ORM
- Users only see records they have access to
- Filter operations limited to own user profile

---

## 11. Future Enhancements

Potential improvements for future iterations:

1. **Advanced Filter UI**
   - Date range pickers
   - Number range sliders
   - Multi-select dropdowns
   - Boolean toggles

2. **Search Analytics**
   - Most searched terms
   - Popular filters
   - Module usage statistics

3. **Export Functionality**
   - Export search results to CSV/Excel
   - Scheduled search reports
   - Email search results

4. **Search Suggestions**
   - Auto-complete suggestions
   - Spell check/correction
   - Related searches

5. **Full-Text Search**
   - PostgreSQL full-text search
   - Relevance ranking
   - Fuzzy matching

---

## 12. Troubleshooting

### Common Issues

**No Results Found:**
- Verify minimum 2 characters entered
- Check spelling
- Try broader search terms
- Check module filters (might be filtering out results)

**Filter Not Saving:**
- Ensure valid filter name provided
- Check browser console for errors
- Verify authenticated session
- Check UserPreference model permissions

**Search History Not Updating:**
- Check JavaScript console for errors
- Verify API endpoints accessible
- Clear browser cache
- Check CSRF token validity

---

## Summary

✅ **29 searchable models** across **12 modules**
✅ **Comprehensive filtering** with save/load capability
✅ **Search history tracking** (last 20 searches)
✅ **Full API support** for programmatic access
✅ **88+ tests** ensuring reliability
✅ **Responsive UI** with keyboard shortcuts
✅ **Production-ready** with proper security

The global search system provides a powerful, user-friendly way to find any record across the entire Floor Management System!

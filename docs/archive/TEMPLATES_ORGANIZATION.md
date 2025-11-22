# Templates Organization Documentation

## Overview
This document provides a comprehensive guide to the template organization across the Floor Management System.

## Directory Structure

```
templates/
├── base.html                          # Main base template
├── core/                              # Core app templates
│   ├── main_dashboard.html           # Main system dashboard
│   ├── finance_dashboard.html        # Finance dashboard
│   ├── user_preferences.html         # User settings
│   ├── costcenter_list.html         # Cost center list
│   ├── costcenter_detail.html       # Cost center detail
│   ├── costcenter_form.html         # Cost center form
│   ├── erpreference_list.html       # ERP references
│   ├── lossofsale_list.html         # Loss of sale events
│   ├── lossofsale_detail.html       # Loss event detail
│   ├── lossofsale_form.html         # Loss event form
│   └── django_core/                  # Django core tables UI
│       ├── user_list.html
│       ├── user_detail.html
│       ├── user_form.html
│       ├── group_list.html
│       ├── group_detail.html
│       ├── permission_list.html
│       ├── contenttype_list.html
│       ├── adminlog_list.html
│       └── session_list.html
│
└── floor_app/operations/             # Operations modules
    ├── hr/templates/hr/
    │   ├── person_detail.html        # Enhanced employee detail (5 tabs)
    │   ├── person_form.html
    │   ├── position_list.html        # Position management
    │   ├── position_detail.html
    │   ├── position_form.html
    │   ├── position_confirm_delete.html
    │   ├── department_list.html
    │   ├── department_detail.html
    │   ├── leave/                    # Leave management (12 templates)
    │   │   ├── policy_list.html
    │   │   ├── policy_detail.html
    │   │   ├── policy_form.html
    │   │   ├── request_list.html
    │   │   ├── request_detail.html
    │   │   ├── request_form.html
    │   │   ├── balance_dashboard.html
    │   │   ├── balance_adjust.html
    │   │   ├── balance_initialize.html
    │   │   ├── employee/             # Employee interface
    │   │   │   ├── my_leave.html
    │   │   │   ├── apply_leave.html
    │   │   │   └── leave_detail.html
    │   ├── training/                 # Training management (9 templates)
    │   │   ├── program_list.html
    │   │   ├── program_detail.html
    │   │   ├── program_form.html
    │   │   ├── session_list.html
    │   │   ├── session_detail.html
    │   │   ├── session_form.html
    │   │   ├── my_dashboard.html
    │   │   ├── enroll.html
    │   │   └── complete.html
    │   ├── attendance/               # Attendance tracking (12 templates)
    │   │   ├── record_list.html
    │   │   ├── record_detail.html
    │   │   ├── check_in.html
    │   │   ├── check_out.html
    │   │   ├── overtime_list.html
    │   │   ├── overtime_detail.html
    │   │   ├── overtime_form.html
    │   │   ├── config_list.html
    │   │   ├── config_detail.html
    │   │   ├── config_form.html
    │   │   ├── my_attendance.html
    │   │   └── submit_overtime.html
    │   └── documents/                # Document management
    │       ├── hr/
    │       │   ├── document_list.html
    │       │   ├── document_detail.html
    │       │   ├── upload_document.html
    │       │   └── renewal_list.html
    │       └── employee/
    │           ├── my_documents.html
    │           ├── view_document.html
    │           ├── upload_document.html
    │           └── request_renewal.html
    │
    ├── inventory/templates/inventory/
    │   ├── dashboard.html            # Inventory dashboard
    │   ├── items/
    │   │   ├── list.html
    │   │   ├── detail.html
    │   │   └── form.html
    │   ├── bit_designs/              # Bit design management
    │   │   ├── list.html
    │   │   ├── detail.html
    │   │   ├── form.html             # Bit design form
    │   │   ├── mat_list.html
    │   │   ├── mat_detail.html
    │   │   ├── mat_form.html         # MAT revision form
    │   │   └── tree_node.html
    │   ├── locations/                # Location management
    │   │   ├── list.html             # Tree visualization
    │   │   ├── detail.html
    │   │   ├── form.html
    │   │   └── tree_node.html        # Recursive node template
    │   ├── serial_units/
    │   │   ├── list.html
    │   │   ├── detail.html
    │   │   └── form.html
    │   ├── stock/
    │   │   ├── list.html
    │   │   └── detail.html
    │   ├── boms/
    │   │   ├── list.html
    │   │   ├── detail.html
    │   │   └── form.html
    │   └── transactions/
    │       ├── list.html
    │       └── detail.html
    │
    └── evaluation/templates/evaluation/
        ├── sessions/
        │   ├── list.html
        │   ├── detail.html           # Enhanced with 6 tabs
        │   └── form.html
        ├── grid/
        │   ├── editor.html           # Cutter evaluation grid
        │   └── view.html
        └── reports/
            └── session_report.html
```

---

## Template Patterns

### 1. Base Template (`base.html`)
All templates extend from this base:
- Bootstrap 5.3.3 framework
- Bootstrap Icons
- Responsive navbar
- Block structure:
  - `{% block title %}`
  - `{% block extra_css %}`
  - `{% block breadcrumbs %}`
  - `{% block content %}`
  - `{% block extra_js %}`

### 2. Dashboard Templates
Pattern: `{module}_dashboard.html`

**Features:**
- KPI cards with statistics
- Chart.js visualizations
- Quick action buttons
- Module-specific widgets
- Responsive grid layout

**Examples:**
- `core/main_dashboard.html` - 4 Chart.js charts, 6 module cards
- `inventory/dashboard.html` - Inventory KPIs, alerts, quick actions

### 3. List Templates
Pattern: `{model}_list.html`

**Standard Structure:**
```html
{% extends 'base.html' %}

{% block content %}
<!-- Header with title and action buttons -->
<!-- Statistics/KPI cards -->
<!-- Filters form -->
<!-- Data table/cards -->
<!-- Pagination -->
{% endblock %}
```

**Common Features:**
- Search functionality
- Multiple filter dropdowns
- Sort options
- Pagination
- Create button
- Statistics summary
- Responsive cards or tables

**Examples:**
- `hr/position_list.html` - Color-coded position cards
- `inventory/locations/list.html` - Tree visualization

### 4. Detail Templates
Pattern: `{model}_detail.html`

**Standard Structure:**
```html
{% extends 'base.html' %}

{% block content %}
<!-- Gradient header with key info -->
<!-- Tabs navigation (if applicable) -->
<!-- Tab content panels -->
<!-- Info cards with sections -->
<!-- Related data tables -->
<!-- Action buttons -->
{% endblock %}
```

**Common Features:**
- Gradient header
- Photo/icon display
- Tabbed interface (for complex entities)
- Info cards with detail rows
- Related data sections
- Edit/Delete buttons
- Back navigation

**Examples:**
- `hr/person_detail.html` - 5 tabs (Overview, Qualifications, Leave, Training, Documents)
- `inventory/bit_designs/detail.html` - Design specs, MAT list
- `evaluation/sessions/detail.html` - 6 tabs with comprehensive data

### 5. Form Templates
Pattern: `{model}_form.html`

**Standard Structure:**
```html
{% extends 'base.html' %}

{% block content %}
<!-- Form container -->
<!-- Form sections with fieldsets -->
<!-- Field rows with labels and inputs -->
<!-- Help text -->
<!-- Submit/Cancel buttons -->
{% endblock %}
```

**Common Features:**
- Organized fieldsets/sections
- Section headers with icons
- Help text for complex fields
- Bootstrap form styling
- Client-side validation
- Cancel button navigation
- Success/error messages

**Examples:**
- `inventory/bit_designs/form.html` - 2 sections (Basic, Technical)
- `inventory/bit_designs/mat_form.html` - 4 sections
- `inventory/locations/form.html` - 4 sections with GPS support

### 6. Tabbed Interfaces
Used for complex entities with multiple data facets.

**Pattern:**
```html
<!-- Nav tabs -->
<ul class="nav nav-tabs">
  <li class="nav-item">
    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab1">
      Tab 1 <span class="badge">{{ count }}</span>
    </button>
  </li>
</ul>

<!-- Tab content -->
<div class="tab-content">
  <div class="tab-pane fade show active" id="tab1">
    <!-- Tab 1 content -->
  </div>
</div>
```

**Examples:**
- Person Detail: Overview, Qualifications, Leave Balance, Training, Documents
- Evaluation Session Detail: Cutter Grid, Thread, NDT, Instructions, Requirements, History

### 7. Tree Visualization Templates
For hierarchical data structures.

**Pattern:**
```html
<!-- Main list template -->
<div id="tree-container">
  {% for node in tree_root %}
    {% include 'recursive_node.html' with node=node level=0 %}
  {% endfor %}
</div>

<!-- Recursive node template -->
<div class="node level-{{ level }}">
  <!-- Node content -->
  {% if node.children %}
    <div class="children">
      {% for child in node.children %}
        {% include 'recursive_node.html' with node=child level=level|add:1 %}
      {% endfor %}
    </div>
  {% endif %}
</div>
```

**Features:**
- Expand/collapse functionality
- Visual indentation
- Color-coded levels
- Toggle icons

**Example:**
- `inventory/locations/list.html` + `tree_node.html`

---

## UI/UX Patterns

### Color Scheme
- **Primary:** #667eea (Purple) - Main actions, headers
- **Info:** #17a2b8 (Cyan) - Inventory, informational
- **Success:** #28a745 (Green) - Active states, success
- **Warning:** #ffc107 (Yellow) - Warnings, pending
- **Danger:** #dc3545 (Red) - Errors, critical items

### Card Styles
1. **KPI Cards** - Statistics with large numbers
2. **Info Cards** - Detailed information sections
3. **Module Cards** - Quick access navigation
4. **Item Cards** - List item representation
5. **Alert Cards** - Warning/error display

### Headers
1. **Gradient Headers** - Main entity headers
   ```css
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   ```
2. **Section Headers** - Within pages
   ```css
   border-left: 4px solid #color;
   ```

### Icons
Bootstrap Icons used throughout:
- `bi-people` - HR/Users
- `bi-box-seam` - Inventory
- `bi-gear` - Production
- `bi-shield-check` - Quality
- `bi-cart` - Sales
- `bi-currency-dollar` - Finance

---

## Chart Integration

### Chart.js 4.4.0
Used in dashboards for data visualization.

**Chart Types Used:**
1. **Doughnut** - Distribution (Module activity)
2. **Bar** - Comparisons (System health, Finance)
3. **Horizontal Bar** - Rankings (Quality metrics)
4. **Line** - Trends (Time series data)

**Pattern:**
```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('myChart').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {...},
    options: {...}
});
</script>
{% endblock %}
```

---

## Responsive Design

### Breakpoints (Bootstrap 5)
- **xs:** <576px - Mobile
- **sm:** ≥576px - Mobile landscape
- **md:** ≥768px - Tablet
- **lg:** ≥992px - Desktop
- **xl:** ≥1200px - Large desktop
- **xxl:** ≥1400px - Extra large

### Grid Usage
```html
<div class="row">
  <div class="col-12 col-md-6 col-lg-4">
    <!-- Responsive column -->
  </div>
</div>
```

### Mobile Considerations
- Stack columns on mobile
- Collapsible filters
- Touch-friendly buttons (min 44px)
- Horizontal scroll for tables
- Responsive navigation

---

## Component Library

### Reusable Components

#### 1. Badge Status
```html
{% if status == 'ACTIVE' %}
  <span class="badge bg-success">Active</span>
{% else %}
  <span class="badge bg-secondary">{{ status }}</span>
{% endif %}
```

#### 2. Detail Row
```html
<div class="detail-row">
  <span class="detail-label">Field Name:</span>
  <span class="detail-value">{{ value }}</span>
</div>
```

#### 3. Action Buttons
```html
<div class="d-flex gap-2">
  <a href="{% url 'app:list' %}" class="btn btn-light">
    <i class="bi bi-arrow-left me-2"></i>Back
  </a>
  <a href="{% url 'app:edit' pk %}" class="btn btn-warning">
    <i class="bi bi-pencil me-2"></i>Edit
  </a>
</div>
```

#### 4. Empty State
```html
<div class="text-center py-5 text-muted">
  <i class="bi bi-inbox" style="font-size: 3rem;"></i>
  <p class="mt-3">No items found</p>
  <a href="{% url 'app:create' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle me-2"></i>Create First Item
  </a>
</div>
```

---

## Best Practices

### 1. Template Inheritance
- Always extend from `base.html`
- Override only necessary blocks
- Keep templates DRY (Don't Repeat Yourself)

### 2. Template Tags
- Use `{% load static %}` for static files
- Use `{% url %}` for all links (never hardcode URLs)
- Use template filters for formatting (`|date`, `|floatformat`, etc.)

### 3. Performance
- Use `select_related` and `prefetch_related` in views
- Limit queryset sizes (pagination)
- Lazy load heavy content (tabs, accordions)
- Optimize images

### 4. Accessibility
- Use semantic HTML
- Include ARIA labels where needed
- Ensure keyboard navigation
- Maintain color contrast ratios

### 5. JavaScript
- Place scripts in `{% block extra_js %}`
- Use CDN for libraries (Chart.js, etc.)
- Initialize on DOMContentLoaded
- Handle errors gracefully

### 6. CSS
- Place styles in `{% block extra_css %}`
- Use Bootstrap utilities first
- Create custom classes only when needed
- Follow BEM naming for custom classes

---

## Template Counts by Module

| Module | List | Detail | Form | Dashboard | Special | Total |
|--------|------|--------|------|-----------|---------|-------|
| Core | 8 | 5 | 3 | 2 | 9 (Django) | 27 |
| HR | 4 | 2 | 2 | 1 | 35 (Leave/Training/Attendance/Docs) | 44 |
| Inventory | 7 | 7 | 6 | 1 | 2 (Tree) | 23 |
| Evaluation | 3 | 1 | 1 | 0 | 3 (Grid) | 8 |
| **Total** | | | | | | **102+** |

---

## Recent Additions (Last Session)

### New Templates Created:
1. `core/main_dashboard.html` - Interactive dashboard with Chart.js
2. `hr/person_detail.html` - 5-tab employee detail view
3. `hr/position_list.html` - Position management list
4. `hr/position_detail.html` - Position detail view
5. `hr/position_form.html` - Position create/edit form
6. `hr/position_confirm_delete.html` - Safe deletion confirmation
7. `inventory/bit_designs/form.html` - Bit design form
8. `inventory/bit_designs/mat_form.html` - MAT revision form
9. `inventory/locations/list.html` - Location tree list
10. `inventory/locations/detail.html` - Location detail
11. `inventory/locations/form.html` - Location form
12. `inventory/locations/tree_node.html` - Recursive tree node

---

## Future Enhancements

### Planned Improvements:
1. **Global Search** - Unified search across all modules
2. **Dark Mode** - Theme switching capability
3. **Print Styles** - Optimized print layouts
4. **Export Functions** - PDF/Excel export from lists
5. **Advanced Filters** - Saved filter presets
6. **Bulk Actions** - Multi-select operations
7. **Real-time Updates** - WebSocket integration
8. **Mobile App Views** - Dedicated mobile templates

---

Last Updated: 2025-11-18

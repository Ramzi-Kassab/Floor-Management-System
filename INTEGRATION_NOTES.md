# Floor Management System - UI Redesign Integration Guide

## Overview

This document provides instructions for integrating the redesigned frontend templates into your Django Floor Management System.

## Files Created/Updated

### Templates

1. **`floor_app/templates/base.html`** - New base layout with sidebar navigation
2. **`floor_app/templates/registration/login.html`** - Modern login page
3. **`floor_app/templates/home.html`** - Dashboard/home page
4. **`floor_app/templates/hr/employee_setup.html`** - Redesigned employee setup page

### Static Files

1. **`floor_app/static/css/app.css`** - Custom styles for the entire application

---

## Required URL Configuration Changes

### 1. Main Project URLs (`floor_mgmt/urls.py`)

Add the following URL patterns to your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    # Home/Dashboard
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # HR App
    path('hr/', include('floor_app.hr.urls', namespace='hr')),

    # Static files (development only)
    # Already configured in your settings
]
```

### 2. HR App URLs (`floor_app/hr/urls.py`)

Make sure your HR URLs have the correct namespace and URL names. Example:

```python
from django.urls import path
from . import views_employee_setup

app_name = 'hr'

urlpatterns = [
    # Employee Setup
    path('employees/', views_employee_setup.employee_setup_list, name='employee_setup_list'),
    path('employees/new/', views_employee_setup.employee_setup_create, name='employee_setup_create'),
    path('employees/<int:pk>/edit/', views_employee_setup.employee_setup_edit, name='employee_setup_edit'),
    # Add other HR URLs as needed
]
```

### 3. Settings Configuration (`floor_mgmt/settings.py`)

Ensure the following settings are configured:

```python
# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'floor_app' / 'static',
]

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'floor_app' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## View Updates Required

### Home View (Optional - Using Generic View)

If you want to create a custom home view instead of using `TemplateView`:

```python
# floor_app/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(views):
    context = {
        # Add any dynamic data you want to display on the dashboard
        # For example:
        # 'total_employees': HREmployee.objects.count(),
        # 'active_operators': HREmployee.objects.filter(is_operator=True, status='Active').count(),
    }
    return render(request, 'home.html', context)
```

Then update your URL:

```python
from floor_app.views import home

urlpatterns = [
    path('', home, name='home'),
    # ...
]
```

### Employee Setup Views

Your existing `views_employee_setup.py` should work with the new template. Make sure it provides these context variables:

- `employee_form` - The employee form instance
- `people_form` - The person form instance
- `phone_formset` - Phone formset
- `email_formset` - Email formset
- `address_formset` - Address formset
- `employee` - The employee instance (when editing)
- `admin_list_url` - URL to the admin list view
- `admin_change_url` - URL to edit in Django admin (optional)

Example context in your view:

```python
context = {
    'employee': employee,
    'employee_form': employee_form,
    'people_form': people_form,
    'phone_formset': phone_formset,
    'email_formset': email_formset,
    'address_formset': address_formset,
    'admin_list_url': reverse('admin:floor_app_hremployee_changelist'),
    'admin_change_url': reverse('admin:floor_app_hremployee_change', args=[employee.pk]) if employee else None,
}
```

---

## Navigation Customization

### Updating Sidebar Links in `base.html`

The sidebar in `base.html` contains placeholder links. Update them to match your actual URL patterns:

```html
<!-- Example: Update this -->
<a class="nav-link" href="{% url 'hr:employee_setup_list' %}">

<!-- To match your actual URL name -->
<a class="nav-link" href="{% url 'your_actual_url_name' %}">
```

Current sidebar sections:

- **Dashboard** - Links to home
- **Human Resources** - Employee Setup, Attendance, Time Tracking
- **Production** - Work Orders, Floor Layout, Production Reports
- **Administration** - Django Admin (only visible to staff)

### Adding New Menu Items

To add a new menu item to the sidebar:

```html
<li class="nav-item">
    <a class="nav-link" href="{% url 'your_url_name' %}">
        <i class="bi bi-icon-name"></i>
        <span>Menu Label</span>
    </a>
</li>
```

Browse Bootstrap Icons at: https://icons.getbootstrap.com/

---

## Template Inheritance

### Making Other Templates Use the New Layout

For any other templates you create, extend `base.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Your Page Title{% endblock %}

{% block breadcrumbs %}
<div class="container-fluid pt-3 pb-2 border-bottom bg-light">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item"><a href="{% url 'core:home' %}">Dashboard</a></li>
            <li class="breadcrumb-item active">Your Page</li>
        </ol>
    </nav>
</div>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Your page content here -->
</div>
{% endblock %}
```

---

## Form Widget Classes

The CSS is designed to work with Django's default form widgets. However, you may want to add Bootstrap classes to your forms:

```python
# In your forms.py
from django import forms

class YourForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = '__all__'
        widgets = {
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'another_field': forms.Select(attrs={'class': 'form-select'}),
            'text_area': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_field': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
```

Or apply classes globally in your form's `__init__` method:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field_name, field in self.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = 'form-check-input'
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = 'form-select'
        else:
            field.widget.attrs['class'] = 'form-control'
```

---

## Static Files Collection

When deploying to production, run:

```bash
python manage.py collectstatic
```

This will collect all static files (including the new `app.css`) into your `STATIC_ROOT` directory.

---

## Testing Checklist

- [ ] Login page works and redirects to dashboard after login
- [ ] Dashboard page displays correctly with all metrics and quick actions
- [ ] Sidebar navigation works on desktop
- [ ] Sidebar toggles correctly on mobile (< 992px width)
- [ ] Employee setup page loads with all tabs
- [ ] Employee setup form saves correctly
- [ ] Tab state persists in localStorage when navigating
- [ ] All formsets (phones, emails, addresses) render correctly
- [ ] Form validation errors display properly
- [ ] Breadcrumbs show correct navigation path
- [ ] User dropdown menu works in top navbar
- [ ] Logout functionality works

---

## Mobile Responsiveness

The design is fully responsive with breakpoints:

- **Desktop**: ≥ 992px (sidebar visible)
- **Tablet**: 768px - 991px (sidebar toggleable)
- **Mobile**: < 768px (sidebar toggleable, stacked layout)

Test on these viewport sizes:

- 1920x1080 (Desktop)
- 1366x768 (Laptop)
- 768x1024 (Tablet)
- 375x667 (Mobile)

---

## Customization Tips

### Changing the Primary Color

Edit the CSS variables in `app.css`:

```css
:root {
  --primary: #your-color-here;
  --primary-dark: #darker-shade;
  --primary-light: #lighter-tint;
}
```

### Adding a Logo

Replace the building icon in the navbar with your logo:

```html
<!-- In base.html, replace: -->
<i class="bi bi-building me-2"></i>

<!-- With: -->
<img src="{% static 'images/logo.png' %}" alt="Logo" height="32">
```

### Customizing Dashboard Metrics

Edit `home.html` to display real data from your database instead of placeholder values.

---

## Support & Further Development

### Adding More Pages

1. Create a new template extending `base.html`
2. Add URL pattern in appropriate `urls.py`
3. Create view function/class
4. Add link in sidebar navigation

### Creating List Views

For employee list pages or other data tables, consider using:

- Django's `ListView` class-based view
- Bootstrap's table component
- Add search and filter functionality

Example list page structure:

```html
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4">
    <div class="card">
        <div class="card-header">
            <h5 class="card-title">Employee List</h5>
        </div>
        <div class="card-body">
            <table class="table table-hover">
                <!-- Your table content -->
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Additional Resources

- **Bootstrap 5 Documentation**: https://getbootstrap.com/docs/5.3/
- **Bootstrap Icons**: https://icons.getbootstrap.com/
- **Django Templates**: https://docs.djangoproject.com/en/5.0/topics/templates/
- **Django Forms**: https://docs.djangoproject.com/en/5.0/topics/forms/

---

## Questions or Issues?

If you encounter any issues:

1. Check browser console for JavaScript errors
2. Verify all URL names match between templates and `urls.py`
3. Ensure static files are being served correctly
4. Check that all required context variables are being passed to templates
5. Verify Bootstrap 5 CDN links are loading (check Network tab in browser dev tools)

---

**Version**: 1.0  
**Last Updated**: November 10, 2025  
**Compatible With**: Django 5.x, Bootstrap 5.3.3
# Skeleton Quick Reference Guide

**For Developers Working with the Floor Management System**

---

## 🚀 Quick Start

### Running the Application
```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Run migrations (first time only)
python manage.py migrate

# Start development server
python manage.py runserver
```

### Access Points
- **Public Home**: http://localhost:8000/
- **Dashboard**: http://localhost:8000/dashboard/ (requires login)
- **Login**: http://localhost:8000/accounts/login/
- **Admin**: http://localhost:8000/admin/

---

## 📁 Key Files & Directories

### Templates
- `templates/base.html` - Master layout (use this!)
- `templates/base_auth.html` - Auth pages layout
- `templates/partials/` - Reusable components
- `templates/accounts/` - Authentication templates
- `templates/core/` - Core app templates
- `templates/404.html`, `403.html`, `500.html` - Error pages

### Static Files
- `static/css/main.css` - Global design system

### Configuration
- `floor_mgmt/settings.py` - Django settings
- `floor_mgmt/urls.py` - Main URL routing
- `core/urls.py` - Core app URLs
- `accounts/urls.py` - Authentication URLs

---

## 🎨 Using the Skeleton in Your Module

### Step 1: Extend base.html
```django
{% extends "base.html" %}
{% load static %}

{% block title %}My Module - FMS{% endblock %}

{% block content %}
<div class="container my-4">
    <h1>My Module</h1>
    <!-- Your content here -->
</div>
{% endblock %}
```

### Step 2: Use CSS Variables
```css
/* In your custom CSS or inline styles */
.my-button {
    background: var(--primary-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-md);
}
```

### Step 3: Use Bootstrap Classes
```html
<div class="card">
    <div class="card-header">
        <h4 class="mb-0"><i class="fas fa-icon"></i> Title</h4>
    </div>
    <div class="card-body">
        Content
    </div>
</div>
```

### Step 4: Add Navigation Link
Edit `templates/partials/_navbar.html`:
```html
<a class="dropdown-item" href="{% url 'mymodule:dashboard' %}">
    <i class="fas fa-icon"></i> My Module
</a>
```

---

## 🎨 Design System

### Colors (CSS Variables)
```css
--primary-color: #667eea      /* Purple-blue */
--secondary-color: #764ba2    /* Deep purple */
--success-color: #10b981      /* Green */
--warning-color: #f59e0b      /* Orange */
--danger-color: #ef4444       /* Red */
--info-color: #3b82f6         /* Blue */
```

### Spacing Scale
```css
--spacing-xs: 0.25rem    /* 4px */
--spacing-sm: 0.5rem     /* 8px */
--spacing-md: 1rem       /* 16px */
--spacing-lg: 1.5rem     /* 24px */
--spacing-xl: 2rem       /* 32px */
--spacing-2xl: 3rem      /* 48px */
```

### Shadows
```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--shadow-md: 0 4px 6px rgba(0,0,0,0.1)
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1)
--shadow-xl: 0 20px 25px rgba(0,0,0,0.15)
```

### Border Radius
```css
--radius-sm: 0.25rem
--radius-md: 0.5rem
--radius-lg: 1rem
--radius-xl: 1.5rem
```

---

## 🔐 Authentication Helpers

### Require Login
```python
from django.contrib.auth.decorators import login_required

@login_required
def my_view(request):
    # Only logged-in users can access
    pass
```

### Check in Templates
```django
{% if user.is_authenticated %}
    <p>Welcome, {{ user.get_full_name }}!</p>
{% else %}
    <a href="{% url 'login' %}">Login</a>
{% endif %}
```

### Check if Staff
```django
{% if user.is_staff %}
    <a href="{% url 'admin:index' %}">Admin Panel</a>
{% endif %}
```

---

## 📊 Dashboard Cards

### Stats Card
```html
<div class="stats-card">
    <div class="stats-icon">
        <i class="fas fa-users"></i>
    </div>
    <div class="stats-content">
        <div class="stats-label">Total Users</div>
        <div class="stats-value">1,234</div>
    </div>
</div>
```

### Module Card
```html
<div class="module-card">
    <i class="fas fa-icon fa-3x text-primary mb-3"></i>
    <h5 class="card-title">Module Name</h5>
    <p class="card-text">Description of what this module does.</p>
    <a href="{% url 'module:dashboard' %}" class="btn btn-primary btn-sm">
        <i class="fas fa-arrow-right"></i> Open
    </a>
</div>
```

---

## 🔗 Common URL Patterns

### Redirecting to Login
```python
from django.shortcuts import redirect

def my_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
```

### Reversing URLs
```python
from django.urls import reverse

# In views
url = reverse('core:dashboard')

# In templates
{% url 'core:dashboard' %}
{% url 'accounts:profile' %}
{% url 'mymodule:detail' pk=object.pk %}
```

---

## 💬 Messages Framework

### In Views
```python
from django.contrib import messages

def my_view(request):
    messages.success(request, 'Operation successful!')
    messages.error(request, 'Something went wrong.')
    messages.warning(request, 'Please check this.')
    messages.info(request, 'For your information.')
```

### In Templates
```django
<!-- Messages are automatically displayed via partials/_messages.html -->
<!-- No need to add anything, just use messages in views -->
```

---

## 🎯 Common Patterns

### List View
```python
from django.views.generic import ListView

class MyItemListView(ListView):
    model = MyItem
    template_name = 'myapp/item_list.html'
    context_object_name = 'items'
    paginate_by = 20
```

### Detail View
```python
from django.views.generic import DetailView

class MyItemDetailView(DetailView):
    model = MyItem
    template_name = 'myapp/item_detail.html'
    context_object_name = 'item'
```

### Create View
```python
from django.views.generic import CreateView
from django.urls import reverse_lazy

class MyItemCreateView(CreateView):
    model = MyItem
    template_name = 'myapp/item_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('myapp:list')
```

---

## 🐛 Common Issues & Solutions

### Issue: Template not found
**Solution**: Make sure your app is in `INSTALLED_APPS` and templates are in `app_name/templates/app_name/`

### Issue: Static files not loading
**Solution**:
```bash
python manage.py collectstatic
```
Or make sure `STATICFILES_DIRS` is set correctly.

### Issue: CSS changes not showing
**Solution**: Hard refresh browser (Ctrl+Shift+R) or clear browser cache

### Issue: Login redirects to wrong page
**Solution**: Check `LOGIN_REDIRECT_URL` in settings.py

### Issue: Permission denied
**Solution**: Use `@login_required` decorator or check user permissions:
```python
from django.contrib.auth.decorators import permission_required

@permission_required('myapp.view_mymodel')
def my_view(request):
    pass
```

---

## 📝 Template Blocks Reference

### base.html Blocks
```django
{% block title %}{% endblock %}           <!-- Page title -->
{% block extra_css %}{% endblock %}       <!-- Additional CSS -->
{% block content %}{% endblock %}         <!-- Main content -->
{% block extra_js %}{% endblock %}        <!-- Additional JS -->
{% block main_class %}{% endblock %}      <!-- Main container class -->
```

### base_auth.html Blocks
```django
{% block title %}{% endblock %}           <!-- Page title -->
{% block auth_content %}{% endblock %}    <!-- Auth form content -->
```

---

## 🚦 URL Naming Convention

- **App namespace**: Use in `urls.py`: `app_name = 'myapp'`
- **URL names**: Use descriptive names:
  - List: `'myapp:item_list'`
  - Detail: `'myapp:item_detail'`
  - Create: `'myapp:item_create'`
  - Update: `'myapp:item_update'`
  - Delete: `'myapp:item_delete'`
  - Dashboard: `'myapp:dashboard'`

---

## 🔧 Development Tips

1. **Always extend base.html** for consistent look
2. **Use CSS variables** instead of hardcoded colors
3. **Add Font Awesome icons** for better UX
4. **Use Django messages** for user feedback
5. **Test on mobile** - Bootstrap is responsive
6. **Use semantic HTML** - helps with accessibility
7. **Keep templates DRY** - use includes and partials
8. **Name URLs** - never hardcode URLs in templates

---

## 📚 Resources

- **Bootstrap 5 Docs**: https://getbootstrap.com/docs/5.3/
- **Font Awesome Icons**: https://fontawesome.com/icons
- **Django Docs**: https://docs.djangoproject.com/
- **Django Template Language**: https://docs.djangoproject.com/en/5.2/ref/templates/language/

---

**Last Updated**: November 22, 2025
**Phase**: 2.5 - Core Skeleton
**Status**: Ready for Use

# Floor Management System - Project Analysis

**Date**: November 13, 2025
**Project**: Floor Management System (Django 5.2 + Bootstrap 5)

## 1. CURRENT VIEWS

### File: floor_app/views.py
- home() - Dashboard (requires login)
  - URL: / 
  - Method: GET
  - Returns: Rendered home.html
  - Context: None (can add metrics)

### File: floor_app/hr/views_employee_setup.py

**employee_setup(request, employee_id=None)**
- URL: GET/POST /hr/employees/setup/new/ OR /hr/employees/setup/<id>/
- Purpose: Create/edit employee wizard
- Forms: HRPeopleForm, HREmployeeForm
- Formsets: Phones, Emails, Addresses
- Context:
  - employee, is_new
  - people_form, employee_form
  - phone_formset, email_formset, address_formset
  - admin_list_url, admin_change_url

**employee_setup_list(request)**
- URL: GET /hr/employees/setup/
- Status: Login required
- Purpose: Entry point - redirects to new employee setup
- Future: Should show employee list

## 2. TEMPLATES

### base.html - Master Layout
- Fixed navbar (64px) with logo and user menu
- Fixed sidebar (260px) with navigation
- Mobile responsive (sidebar toggle < 992px)
- Bootstrap 5.3.3 + Bootstrap Icons
- Blocks: title, extra_css, breadcrumbs, content, extra_js

**Sidebar Items**:
- Dashboard
- Human Resources (Employee Setup, Attendance, Time Tracking)
- Production (Work Orders, Floor Layout, Reports)
- Admin (Django Admin - staff only)

### home.html - Dashboard
- Extends base.html
- Welcome section with user greeting
- 4 Metric cards (placeholder data)
- 6 Quick action buttons
- Recent activity feed (5 items)
- System status indicator
- **Note**: All data is hardcoded placeholder

### login.html - Login
- Standalone page (no inheritance)
- Gradient purple background
- Card-based form
- Fields: username, password, remember me
- Modern glassmorphism design

### employee_setup.html - Wizard
- Extends base.html
- 5 tabs: Employee, Person, Phones, Emails, Addresses
- Tab state persists in localStorage
- Formsets for contact info
- Inline error messages
- Cancel/Save buttons

### admin/hremployee/ - Custom Admin
- change_list.html - Employee list
- change_form.html - Employee edit form

## 3. STATIC FILES

### CSS: app.css (942 lines)
- Bootstrap 5 base
- Custom variables (colors, spacing, layout)
- Navbar styles
- Sidebar styles (fixed, toggle on mobile)
- Cards, badges, forms, buttons
- Dashboard metrics styling
- Formset card styling
- Responsive design (@media queries)
- Colors: Primary blue, success green, danger red, etc.
- Layout: sidebar 260px, navbar 64px

### JavaScript
- hr_admin.js - HR admin helpers
- hr_address_admin.js - Address validation
- hr_people_dob_sync.js - Date conversion

### External
- Bootstrap 5.3.3 (CDN)
- Bootstrap Icons 1.11.3 (CDN)

## 4. FORMS

### HRPeopleForm
- Model: HRPeople
- Includes: Names (EN/AR), gender, nationality, IDs, DoB, photo
- Excludes: Audit fields, public_id, soft delete fields

### HREmployeeForm
- Model: HREmployee
- Fields: user, employee_no, status, job_title, team, is_operator, hire_date, termination_date

### Formsets (InlineFormsetFactory)
- HRPhoneFormSet: Multiple phones per person
- HREmailFormSet: Multiple emails per person
- HRAddressFormSet: Multiple addresses per person
- Features: extra=1, can_delete=True, exclude audit fields

## 5. MODELS & RELATIONSHIPS

### HRPeople
- Canonical person record
- Fields: English/Arabic names, preferred names, gender, nationality, DOB (Gregorian/Hijri)
- IDs: national_id (unique), iqama_number (unique if provided)
- Photo: ImageField
- name_dob_hash: SHA1 for deduplication
- Mixins: PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin
- Relations: HREmployee (1-to-1), HRPhone/Email/Address (1-to-many)

### HREmployee
- Employment record
- Fields: person (1-to-1), user (optional), employee_no (unique), status, job_title, team, is_operator
- Dates: hire_date, termination_date
- Mixins: PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin
- Properties: phones, emails, addresses (convenience accessors)

### HRPhone, HREmail, HRAddress
- Contact info records
- Each has FK to HRPeople
- Phone: phone_e164, country_iso2, kind, use
- Email: email, kind, is_verified
- Address: address_line1/2, city, state, postal_code, country_iso2, kind, use

### HRQualification
- Skill/certification definition
- Fields: code (unique), name, issuer_type, level, validity_months, is_active

### HREmployeeQualification
- Track employee certifications
- Fields: employee (FK), qualification (FK), status, issued_at, expires_at

## 6. AUTHENTICATION

- Framework: Django's built-in auth
- Login: /accounts/login/ → registration/login.html
- Logout: /accounts/logout/
- Protected: home() has @login_required
- Not protected: employee_setup() (should be)
- Staff features: Django Admin link ({% if user.is_staff %})

## 7. ADMIN INTERFACE

Registered models:
- HRPeopleAdmin: list_display (ID, names, IDs), search, autocomplete
- HRPhoneAdmin: list_display, filters (kind, use, country), search, autocomplete person
- HREmailAdmin: list_display, filters, search, autocomplete person
- HRAddressAdmin: list_display, filters, search, autocomplete person
- HREmployeeAdmin: custom templates, list_display, filters, search, autocomplete
- HRQualificationAdmin: list_display, filters, search
- HREmployeeQualificationAdmin: list_display, filters, search, autocomplete

## FEATURES IMPLEMENTED
- Modern responsive UI (Bootstrap 5)
- Login/logout authentication
- Multi-step employee setup wizard
- Formset support (inline editing)
- Admin interface
- Soft delete support
- Audit trails
- Phone/Email/Address management
- KSA support (Hijri calendar, national ID, IQAMA)
- UUID public IDs

## HIGH PRIORITY FEATURES NEEDED
1. Employee list view (proper list with search/filter)
2. Dashboard data integration (real metrics from DB)
3. Add @login_required to employee_setup views
4. Form field Bootstrap CSS classes
5. Search and advanced filters

## MEDIUM PRIORITY FEATURES
6. Attendance module
7. Time tracking
8. Work orders
9. Production reports
10. Floor layout management

## ARCHITECTURE
- Django 5.2 project structure
- Models with proper relationships
- Forms and formsets for complex data
- Templates with Bootstrap 5
- CSS custom properties for theming
- JavaScript for interactivity
- Admin configuration for management


# Departments Feature - Quick Start

## 3-Step Setup

### 1️⃣ Apply Migration
```bash
python manage.py migrate
```

### 2️⃣ Load Sample Data
```bash
python manage.py loaddata floor_app/fixtures/departments.json
```

### 3️⃣ Start Server & Access
```bash
python manage.py runserver
```

Then open: **`http://127.0.0.1:8000/hr/departments/`**

---

## What You Get

### ✨ 10 Pre-populated Departments

**Production (3)**
- PDC Production and Repair
- Roller Cones
- Infiltration

**Support (4)**
- Quality
- Safety
- Requirements
- Logistics
- Technical

**Management (2)**
- Human Resource
- Sales

---

## Features Included

✅ List all departments with search and filtering
✅ Create new departments
✅ View department details
✅ Edit department information
✅ Delete departments with confirmation
✅ Glassmorphism UI design matching dashboard
✅ Responsive mobile-friendly layout
✅ Department type categorization
✅ Statistics overview
✅ Sidebar navigation link

---

## Key Pages

| Page | URL |
|------|-----|
| List | `/hr/departments/` |
| Create | `/hr/departments/create/` |
| View | `/hr/departments/{id}/` |
| Edit | `/hr/departments/{id}/edit/` |
| Delete | `/hr/departments/{id}/delete/` |

---

## Files Created/Updated

### New Files
- ✨ `floor_app/hr/models/department.py`
- ✨ `floor_app/hr/views_department.py`
- ✨ `floor_app/migrations/0017_create_department.py`
- ✨ `floor_app/fixtures/departments.json`
- ✨ `floor_app/templates/hr/department_list.html`
- ✨ `floor_app/templates/hr/department_detail.html`
- ✨ `floor_app/templates/hr/department_form.html`
- ✨ `floor_app/templates/hr/department_confirm_delete.html`

### Updated Files
- 📝 `floor_app/hr/urls.py` - Added department routes
- 📝 `floor_app/templates/base.html` - Updated sidebar link
- 📝 `floor_app/hr/models/__init__.py` - Added department import

---

## Database Commands

```bash
# Check migration status
python manage.py showmigrations floor_app

# Apply migrations
python manage.py migrate

# Load sample departments
python manage.py loaddata floor_app/fixtures/departments.json

# Interactive Python shell
python manage.py shell

# Inside shell:
from floor_app.hr.models import Department
Department.objects.all()  # See all departments
Department.objects.filter(department_type='PRODUCTION')  # Filter by type
```

---

## Admin Access

After migration, you can also manage departments via Django admin:

1. Go to: `/admin/`
2. Navigate to: **Floor_app → Departments**
3. Add/Edit/Delete departments

---

## Styling Details

- **Primary Color**: #6366f1 (Indigo)
- **Production Icon**: ⚙️ Gear (#f59e0b)
- **Support Icon**: 🎧 Headset (#10b981)
- **Management Icon**: 👤 Person (#6366f1)
- **Design Pattern**: Glassmorphism with animations

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No such table" error | Run: `python manage.py migrate` |
| Departments not showing | Run: `python manage.py loaddata floor_app/fixtures/departments.json` |
| 404 on departments link | Make sure you're accessing `/hr/departments/` (with /hr prefix) |
| Can't edit/delete | Make sure you're logged in |
| Sidebar link broken | Restart server after migration |

---

## Next Steps

After the departments feature is working:

1. Link employees to departments
2. Add department-specific analytics
3. Create department reports
4. Set up department hierarchies
5. Add attendance tracking per department

---

**Status**: ✅ Ready to Use

Follow the 3-Step Setup above to get started!

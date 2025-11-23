# Core System Module

Enterprise-grade audit logging, monitoring, and system administration for Floor Management System.

## 📋 Overview

The Core module provides comprehensive audit trails, activity tracking, system monitoring, and administrative tools for the entire application.

## 🎯 Features

### Audit Logging
- **Complete Audit Trail**: Track all model changes (CREATE, UPDATE, DELETE)
- **User Tracking**: Record who made changes, when, and from where
- **IP Address Logging**: Track the source of all actions
- **Change History**: Before/after snapshots of model changes
- **Automatic Logging**: No code changes needed - uses Django signals

### Activity Monitoring
- **User Activity Tracking**: Monitor user navigation and actions
- **Performance Metrics**: Track request duration and slow queries
- **Activity Analytics**: Understand usage patterns
- **Top Users/Paths**: Identify most active users and visited pages

### System Monitoring
- **Health Checks**: Real-time system health status
- **Error Tracking**: Automatic capture of exceptions and errors
- **Event Logging**: System-level events with categorization
- **Alert Management**: Unresolved events tracking

### Permissions & Security
- **Custom Permissions**: Row-level and department-based access control
- **DRF Permission Classes**: Ready-to-use REST framework permissions
- **Security Events**: Failed login tracking
- **Permission Helpers**: Utility functions for complex permission checks

### Data Export
- **Multiple Formats**: Excel, PDF, CSV
- **Professional Formatting**: Branded PDFs, styled Excel sheets
- **Bulk Export**: Background task support for large datasets
- **Convenience Functions**: Easy queryset-to-file exports

### Background Tasks
- **Celery Integration**: Async task processing
- **Scheduled Tasks**: Automated maintenance and reporting
- **Email Notifications**: Automated alerts and summaries
- **Report Generation**: Background report creation

### Management Commands
- **check_system_health**: Monitor system health with detailed metrics
- **cleanup_logs**: Automated log cleanup with retention policies
- **generate_activity_report**: Activity analytics with export support

## 📂 Module Structure

```
floor_app/core/
├── models.py              # Core models (AuditLog, ActivityLog, etc.)
├── middleware.py          # Custom middleware for tracking
├── admin.py              # Admin interfaces
├── views.py              # Dashboard and monitoring views
├── urls.py               # URL patterns
├── signals.py            # Signal handlers for auto-audit
├── permissions.py        # Custom permission classes
├── validators.py         # Custom validators and mixins
├── utils.py              # Utility functions
├── exports.py            # Data export utilities
├── tasks.py              # Celery tasks
├── context_processors.py # Template context processors
├── management/
│   └── commands/
│       ├── check_system_health.py
│       ├── cleanup_logs.py
│       └── generate_activity_report.py
└── migrations/
```

## 🔧 Installation

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'floor_app.core',
    # ...
]
```

### 2. Add Middleware

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware ...
    'floor_app.core.middleware.ActivityTrackingMiddleware',
    'floor_app.core.middleware.AuditTrailMiddleware',
    'floor_app.core.middleware.RequestTimingMiddleware',
    'floor_app.core.middleware.ErrorMonitoringMiddleware',
]
```

### 3. Add Context Processors (Optional)

```python
# settings.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ... other processors ...
            'floor_app.core.context_processors.system_status',
            'floor_app.core.context_processors.user_activity',
        ],
    },
}]
```

### 4. Configure Celery (Optional)

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### 5. Run Migrations

```bash
python manage.py makemigrations floor_core
python manage.py migrate floor_core
```

### 6. Include URLs

```python
# floor_mgmt/urls.py
urlpatterns = [
    # ...
    path('core/', include('floor_app.core.urls')),
    # ...
]
```

## 📖 Usage

### Automatic Audit Logging

All model changes are automatically logged. No code changes needed!

```python
# Just use your models normally
employee = Employee.objects.create(
    employee_code='EMP001',
    # ...
)
# ✓ CREATE action automatically logged

employee.employment_status = 'TERMINATED'
employee.save()
# ✓ UPDATE action automatically logged

employee.delete()
# ✓ DELETE action automatically logged
```

### Manual Audit Logging

```python
from floor_app.core.models import AuditLog

AuditLog.log_action(
    user=request.user,
    action='APPROVE',
    obj=leave_request,
    message='Approved leave request',
    ip_address=request.META.get('REMOTE_ADDR'),
)
```

### Change Tracking

```python
from floor_app.core.utils import ChangeTracker

# Track changes to a model instance
with ChangeTracker(employee, user=request.user, reason='Annual review'):
    employee.salary = 60000
    employee.position = new_position
    employee.save()
# Changes automatically tracked and logged
```

### System Health Check

```bash
# Command line
python manage.py check_system_health --detailed

# In code
from floor_app.core.utils import get_system_health_summary

health = get_system_health_summary()
if health['health_status'] == 'CRITICAL':
    send_alert()
```

### Activity Reports

```bash
# Generate activity report
python manage.py generate_activity_report --days 30 --export excel

# Filter by user
python manage.py generate_activity_report --user admin --export pdf
```

### Log Cleanup

```bash
# Dry run (preview what would be deleted)
python manage.py cleanup_logs --days 90 --dry-run

# Actual cleanup
python manage.py cleanup_logs --days 90
```

### Data Export

```python
from floor_app.core.exports import export_queryset_to_excel

# Export queryset to Excel
return export_queryset_to_excel(
    Employee.objects.all(),
    'employees.xlsx',
    fields=['employee_code', 'person__first_name', 'department__name'],
    headers=['Code', 'Name', 'Department']
)
```

### Custom Permissions

```python
from rest_framework.decorators import api_view, permission_classes
from floor_app.core.permissions import CanAccessHRData

@api_view(['GET'])
@permission_classes([CanAccessHRData])
def employee_list(request):
    # Only users with HR access can see this
    ...
```

### Background Tasks

```python
from floor_app.core.tasks import send_notification_email

# Queue email for background sending
send_notification_email.delay(
    subject='Welcome!',
    message='Welcome to the system',
    recipient_list=['user@example.com']
)
```

## 🌐 URLs

### Dashboard & Viewers
- `/core/dashboard/` - System monitoring dashboard
- `/core/activity-logs/` - Activity logs viewer
- `/core/audit-logs/` - Audit logs viewer
- `/core/system-events/` - System events viewer
- `/core/user-activity/<username>/` - Individual user activity report

### Export Endpoints
- `/core/export/activity-logs/?format=excel` - Export activity logs
- `/core/export/audit-logs/?format=pdf` - Export audit logs

### API Endpoints
- `/core/api/health/` - System health JSON
- `/core/api/activity-stats/` - Activity statistics JSON
- `/core/api/audit-stats/` - Audit statistics JSON

## 📊 Models

### AuditLog
Complete audit trail with user, action, IP tracking.

**Fields**: user, username, content_type, object_id, action, field_name, old_value, new_value, timestamp, ip_address, user_agent, message

**Actions**: CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, APPROVE, REJECT, EXPORT, IMPORT

### ChangeHistory
Detailed before/after snapshots of model changes.

**Fields**: content_type, object_id, field_changes (JSON), changed_by, changed_at, change_reason

### ActivityLog
User activity tracking for monitoring and analytics.

**Fields**: user, activity_type, path, timestamp, duration_ms, ip_address, query_params (JSON)

**Activity Types**: PAGE_VIEW, SEARCH, FILTER, DOWNLOAD, UPLOAD, API_CALL, REPORT, PRINT

### SystemEvent
System-level events and errors.

**Fields**: level, category, event_name, message, exception details, timestamp, user

**Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Categories**: SYSTEM, SECURITY, DATABASE, EMAIL, API, TASK, INTEGRATION

## 🎨 Validators & Mixins

### Validators
- `validate_phone_number` - Phone number format validation
- `validate_employee_code` - Employee code format (EMP + 6 digits)
- `validate_date_range` - Date range validation
- `validate_no_overlap` - Prevent overlapping date ranges

### Model Mixins
- `SoftDeleteMixin` - Soft delete functionality
- `AuditMixin` - Track created_by and updated_by
- `ValidateModelMixin` - Auto-call full_clean() before save
- `CodeGeneratorMixin` - Auto-generate unique codes

## ⚙️ Configuration

### Email Settings
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Floor Management System <noreply@example.com>'
```

### Celery Settings
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

### Logging Settings
```python
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'floor_mgmt.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
}
```

## 📝 Scheduled Tasks

Configured in `floor_mgmt/celery.py`:

- **Weekly**: Cleanup old logs (Sunday 2 AM)
- **Daily**: Activity summary emails (6 PM)
- **Daily**: Check expiring contracts (9 AM)
- **Bi-weekly**: Pending leave reminders (Mon/Thu 10 AM)
- **Weekly**: Generate reports (Monday 8 AM)
- **Every 30 min**: System health check

## 🔒 Security

- IP address logging for all actions
- Failed login attempt tracking
- User agent capture
- Session key tracking
- Automatic security event logging
- Permission-based access to monitoring tools

## 📈 Performance

- Indexed database fields for fast queries
- Pagination for large datasets
- Background task processing for heavy operations
- Configurable log retention
- Efficient queryset operations

## 🧪 Testing

```bash
# Run core module tests
python manage.py test floor_app.core

# Check system health
python manage.py check_system_health

# Generate test data
python manage.py generate_test_data
```

## 📚 Dependencies

- Django 5.2+
- djangorestframework 3.15+
- celery 5.3+ (optional, for background tasks)
- redis 5.0+ (optional, for Celery broker)
- openpyxl 3.1+ (for Excel export)
- reportlab 4.0+ (for PDF export)

## 🤝 Contributing

This module is part of the Floor Management System. For contributions:
1. Follow the existing code style
2. Add tests for new features
3. Update this README
4. Submit pull request

## 📄 License

Part of Floor Management System - MIT License

## 👥 Support

For issues or questions:
- Check the documentation
- Review admin interface
- Run health checks
- Contact system administrators

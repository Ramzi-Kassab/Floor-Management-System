# Floor Management System - Core Monitoring & Audit System

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [Models Reference](#models-reference)
- [Middleware](#middleware)
- [Admin Interface](#admin-interface)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Core Monitoring & Audit System provides enterprise-grade tracking, monitoring, and auditing capabilities for the Floor Management System. It offers comprehensive visibility into system operations, user activities, and data changes.

### Key Capabilities
- **Automatic Audit Logging**: Track all model changes (CREATE, UPDATE, DELETE)
- **Activity Monitoring**: Monitor user activities and system usage patterns
- **System Event Tracking**: Capture errors, warnings, and critical system events
- **User Notifications**: In-app and email notification system
- **Theme Customization**: User-specific theme and accessibility preferences
- **REST API**: Full API access to all monitoring data
- **Export Functionality**: Export logs to Excel, PDF, and CSV formats

## ✨ Features

### 1. Audit Logging
- Automatic tracking of all model changes via Django signals
- Before/after value capture for data modifications
- IP address and user agent tracking
- Field-level change tracking
- Complete audit trail with timestamps

### 2. Activity Monitoring
- User session tracking
- Page view analytics
- Request duration monitoring
- Search and filter activity tracking
- API call logging

### 3. System Event Management
- Error and exception tracking
- Warning and critical event logging
- Automatic categorization (System, Security, Database, Email, API, Task, Integration)
- Event resolution workflow
- Stack trace capture

### 4. Notifications
- Multi-channel support (In-app, Email, Push, SMS)
- User notification preferences
- Notification types: Info, Success, Warning, Error, System
- Quiet hours support
- Bulk notification actions

### 5. Theme & Accessibility
- Light/Dark/Auto mode
- 6 color schemes (Blue, Green, Purple, Orange, Red, Teal)
- 4 font sizes
- Dyslexia-friendly font option
- High contrast mode
- Reduce motion support
- Screen reader optimization
- WCAG 2.1 AA compliance

## 🏗️ Architecture

### Directory Structure
```
floor_app/core/
├── __init__.py
├── apps.py
├── models.py                   # AuditLog, ActivityLog, SystemEvent, ChangeHistory
├── admin.py                    # Admin interfaces
├── notifications.py            # Notification models
├── theme_preferences.py        # User theme models
├── middleware.py               # 4 custom middleware classes
├── signals.py                  # Automatic audit signal handlers
├── permissions.py              # Permission helpers
├── validators.py               # Custom validators
├── utils.py                    # Helper functions
├── exports.py                  # Export utilities
├── tasks.py                    # Celery tasks
├── context_processors.py       # Template context processors
├── urls.py                     # View URLs
├── views.py                    # Dashboard and log views
├── api/
│   ├── __init__.py
│   ├── serializers.py         # DRF serializers
│   ├── views.py               # API ViewSets
│   └── urls.py                # API URLs
├── management/
│   └── commands/
│       ├── check_system_health.py
│       ├── cleanup_logs.py
│       └── generate_activity_report.py
├── migrations/
│   └── 0001_initial.py
├── templates/core/
│   ├── base_responsive.html   # Responsive base template
│   ├── dashboard.html         # Main monitoring dashboard
│   ├── audit_logs.html        # Audit log viewer
│   ├── activity_logs.html     # Activity log viewer
│   ├── system_events.html     # System events viewer
│   └── theme_settings.html    # User theme settings
└── tests/
    └── test_models.py         # Unit tests
```

### Data Flow
```
User Action
    ↓
Middleware (Request Tracking)
    ↓
View/API Handler
    ↓
Model Change (Create/Update/Delete)
    ↓
Django Signal (post_save, post_delete)
    ↓
Audit Log Creation
    ↓
Background Tasks (Celery)
    ↓
Notifications / Reports
```

## 📦 Installation

### Prerequisites
- Python 3.10+
- Django 5.2+
- PostgreSQL (recommended) or SQLite for development
- Redis (for Celery background tasks - optional)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
```
Django>=5.2
djangorestframework>=3.15
django-filter>=25.2
drf-spectacular>=0.29
django-import-export>=4.3
celery>=5.5         # Optional, for background tasks
redis>=7.1          # Optional, for Celery
openpyxl>=3.1       # Optional, for Excel export
reportlab>=4.4      # Optional, for PDF export
```

### Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ... other apps
    'floor_app.core',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'import_export',
]
```

### Add Middleware
```python
MIDDLEWARE = [
    # ... other middleware
    'floor_app.core.middleware.ActivityTrackingMiddleware',
    'floor_app.core.middleware.AuditTrailMiddleware',
    'floor_app.core.middleware.RequestTimingMiddleware',
    'floor_app.core.middleware.ErrorMonitoringMiddleware',
]
```

### Add Context Processors
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other processors
                'floor_app.core.context_processors.system_status',
                'floor_app.core.context_processors.user_activity',
            ],
        },
    },
]
```

### Run Migrations
```bash
python manage.py migrate floor_core
```

### Create Superuser
```bash
python manage.py createsuperuser
```

## ⚙️ Configuration

### Settings.py Configuration

#### REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

#### DRF Spectacular
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Floor Management System API',
    'DESCRIPTION': 'Enterprise Floor Management System with comprehensive REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
}
```

#### Celery (Optional)
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

#### Email Configuration
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Floor Management System <noreply@example.com>'
```

### URL Configuration

Add to your main urls.py:
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Core System URLs
    path("system/", include(("floor_app.core.urls", "floor_core"), namespace="floor_core")),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Core API
    path("api/core/", include("floor_app.core.api.urls")),
]
```

## 📚 API Documentation

### Available Endpoints

#### API Documentation
- **Swagger UI**: `/api/docs/` - Interactive API documentation
- **ReDoc**: `/api/redoc/` - Alternative API documentation
- **OpenAPI Schema**: `/api/schema/` - Raw OpenAPI schema

#### Core API Endpoints
- **Audit Logs**: `/api/core/audit-logs/`
  - GET: List all audit logs (filterable, paginated)
  - GET /{id}/: Get specific audit log
  - GET /stats/: Get audit statistics

- **Activity Logs**: `/api/core/activity-logs/`
  - GET: List all activity logs
  - GET /{id}/: Get specific activity log
  - GET /recent/: Get recent activities
  - GET /stats/: Get activity statistics

- **System Events**: `/api/core/system-events/`
  - GET: List all system events
  - GET /{id}/: Get specific event
  - POST /{id}/resolve/: Mark event as resolved
  - GET /unresolved/: Get unresolved events
  - GET /stats/: Get event statistics

- **Notifications**: `/api/core/notifications/`
  - GET: List user notifications
  - GET /{id}/: Get specific notification
  - POST /{id}/mark_read/: Mark notification as read
  - POST /mark_all_read/: Mark all notifications as read
  - DELETE /{id}/: Delete notification

- **System Health**: `/api/core/health/`
  - GET: Get overall system health status

### Authentication

All API endpoints require authentication. Use Django session authentication or token authentication.

#### Example: Get Audit Logs
```bash
curl -X GET "https://your-domain.com/api/core/audit-logs/?action=CREATE&days=7" \
  -H "Authorization: Token your-token-here"
```

#### Example: Mark Notification as Read
```bash
curl -X POST "https://your-domain.com/api/core/notifications/123/mark_read/" \
  -H "Authorization: Token your-token-here"
```

### Filtering

#### Audit Logs Filters
- `action`: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT
- `model_name`: Filter by model name
- `username`: Filter by username
- `days`: Time range (1, 7, 30, 90, 180)

#### Activity Logs Filters
- `activity_type`: PAGE_VIEW, SEARCH, FILTER, DOWNLOAD, UPLOAD, API_CALL, REPORT, PRINT
- `user`: Filter by user ID
- `days`: Time range

#### System Events Filters
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `category`: SYSTEM, SECURITY, DATABASE, EMAIL, API, TASK, INTEGRATION
- `is_resolved`: true/false

## 📖 Usage Guide

### Web Interface

#### Dashboard
Access the monitoring dashboard at `/system/dashboard/`

Features:
- System health overview
- Recent audit logs
- Activity statistics
- Unresolved system events
- Quick action buttons

#### Audit Logs Viewer
Access at `/system/audit-logs/`

Features:
- Filter by time range, user, action type, model
- View before/after values
- Export to Excel/PDF/CSV
- Pagination support

#### Activity Logs Viewer
Access at `/system/activity-logs/`

Features:
- Filter by time range, user, activity type
- View request duration
- Export capabilities
- Performance metrics

#### System Events
Access at `/system/events/`

Features:
- Filter by severity, category, status
- Mark events as resolved
- View stack traces
- Event categorization

#### Theme Settings
Access at `/system/theme-settings/`

Features:
- Choose light/dark/auto mode
- Select from 6 color schemes
- Adjust font size
- Enable accessibility options

### Management Commands

#### Check System Health
```bash
python manage.py check_system_health
```
Checks database connectivity, cache, email, and system resources.

#### Cleanup Old Logs
```bash
python manage.py cleanup_logs --days 90
```
Removes audit logs older than specified days (default: 90).

#### Generate Activity Report
```bash
python manage.py generate_activity_report --days 30 --format excel
```
Generates comprehensive activity report.

### Programmatic Usage

#### Create Audit Log
```python
from floor_app.core.models import AuditLog

AuditLog.log_action(
    user=request.user,
    action='CREATE',
    model_name='Employee',
    object_id=employee.pk,
    object_repr=str(employee),
    message='Created new employee record',
    ip_address='192.168.1.1'
)
```

#### Create Notification
```python
from floor_app.core.notifications import Notification

Notification.create_notification(
    user=user,
    title='Welcome!',
    message='Your account has been created successfully.',
    notification_type='SUCCESS',
    send_email=True
)
```

#### Track Activity
```python
from floor_app.core.models import ActivityLog

ActivityLog.objects.create(
    user=request.user,
    activity_type='REPORT',
    path='/reports/sales/',
    description='Generated monthly sales report',
    duration_ms=1500,
    ip_address=request.META.get('REMOTE_ADDR')
)
```

## 📊 Models Reference

### AuditLog
Tracks all system changes with before/after values.

**Fields:**
- `user`: User who performed the action
- `username`: Username (denormalized for deleted users)
- `action`: Action type (CREATE, UPDATE, DELETE, etc.)
- `model_name`: Model class name
- `object_id`: Object primary key
- `object_repr`: String representation
- `field_name`: Changed field name
- `old_value`: Previous value
- `new_value`: New value
- `timestamp`: When the action occurred
- `ip_address`: User's IP address
- `user_agent`: Browser/client information

### ActivityLog
Tracks user activities and system usage.

**Fields:**
- `user`: User who performed the activity
- `activity_type`: Type of activity
- `path`: URL path
- `query_params`: GET/POST parameters
- `description`: Activity description
- `timestamp`: When it occurred
- `duration_ms`: Request duration in milliseconds
- `ip_address`: User's IP address

### SystemEvent
Tracks system errors and events.

**Fields:**
- `level`: Severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `category`: Event category
- `event_name`: Event identifier
- `message`: Event message
- `exception_type`: Exception class name
- `exception_message`: Exception message
- `stack_trace`: Full stack trace
- `timestamp`: When it occurred
- `is_resolved`: Resolution status

### Notification
User notifications.

**Fields:**
- `user`: Recipient user
- `title`: Notification title
- `message`: Notification content
- `notification_type`: Type (INFO, SUCCESS, WARNING, ERROR, SYSTEM)
- `is_read`: Read status
- `send_email`: Whether to send email
- `link`: Optional URL

### UserThemePreference
User theme customization.

**Fields:**
- `theme`: Light/Dark/Auto
- `color_scheme`: Blue/Green/Purple/Orange/Red/Teal
- `font_size`: Small/Medium/Large/Extra-Large
- `high_contrast`: Boolean
- `reduce_motion`: Boolean
- `dyslexia_friendly`: Boolean

## 🔧 Middleware

### ActivityTrackingMiddleware
Automatically tracks all user activities including page views, API calls, and request durations.

### AuditTrailMiddleware
Captures request context (IP, user agent) for audit logging.

### RequestTimingMiddleware
Monitors request performance and logs slow requests (>1 second).

### ErrorMonitoringMiddleware
Captures and logs all exceptions with full stack traces.

## 👨‍💼 Admin Interface

Access at `/admin/`

### Available Admin Interfaces
- **Audit Logs**: Read-only with advanced filtering
- **Activity Logs**: Read-only with performance metrics
- **System Events**: View and resolve events
- **Notifications**: Manage user notifications
- **User Theme Preferences**: View user preferences

### Admin Features
- Colored badges for status/severity
- Advanced filtering and search
- Bulk actions
- Export to CSV
- Date hierarchy navigation
- Read-only fields for security

## 🧪 Testing

### Run Tests
```bash
# Run all core tests
python manage.py test floor_app.core

# Run specific test class
python manage.py test floor_app.core.tests.test_models.AuditLogTestCase

# Run with coverage
coverage run --source='floor_app.core' manage.py test floor_app.core
coverage report
```

### Test Coverage
- AuditLog creation and retrieval
- Activity logging
- System event tracking
- Notification creation and management
- Signal handlers
- Middleware functionality

## 🐛 Troubleshooting

### Common Issues

#### 1. Migrations Not Applying
```bash
python manage.py migrate floor_core --fake-initial
```

#### 2. Middleware Order Issues
Ensure core middleware is placed after Django's built-in middleware but before other custom middleware.

#### 3. Celery Tasks Not Running
```bash
# Check Celery is running
celery -A floor_mgmt worker --loglevel=info

# Check Redis is running
redis-cli ping
```

#### 4. API Returns 403 Forbidden
Ensure user is authenticated and has proper permissions:
```python
# In views.py or api/views.py
permission_classes = [IsAuthenticated]
```

#### 5. Templates Not Loading
Verify `APP_DIRS = True` in TEMPLATES setting and templates are in correct directory.

### Debug Mode

Enable verbose logging in settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'floor_app.core': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📄 License

This is part of the Floor Management System. All rights reserved.

## 🤝 Support

For issues, questions, or contributions, please contact the development team.

---

**Built with ❤️ for enterprise-grade floor management**

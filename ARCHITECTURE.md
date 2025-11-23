# Floor Management System - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Technology Stack](#technology-stack)
4. [Module Architecture](#module-architecture)
5. [Database Design](#database-design)
6. [Security Architecture](#security-architecture)
7. [Integration Points](#integration-points)
8. [Deployment Architecture](#deployment-architecture)

## System Overview

The Floor Management System is a comprehensive Enterprise Resource Planning (ERP) solution built using Django framework. It follows a modular, monolithic architecture with clear separation of concerns.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│  (Bootstrap 5 Templates, JavaScript, CSS)               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Application Layer                       │
│  ┌──────────┬──────────┬──────────┬──────────┐         │
│  │    HR    │ Inventory│Engineering│Production│ ...     │
│  │  Module  │  Module  │  Module   │  Module  │         │
│  └──────────┴──────────┴──────────┴──────────┘         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Data Access Layer                      │
│              (Django ORM, Models)                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Database Layer                          │
│                  (PostgreSQL)                            │
└─────────────────────────────────────────────────────────┘
```

## Architecture Patterns

### 1. MTV Pattern (Model-Template-View)

Django's variation of MVC pattern:

- **Models**: Data layer and business logic
- **Templates**: Presentation layer (HTML/CSS)
- **Views**: Controller layer (request handling)

### 2. Modular Monolith

Each business domain is organized as a Django app:

```
floor_app/operations/
├── hr/              # Human Resources
├── hr_portal/       # Employee Self-Service
├── inventory/       # Inventory Management
├── engineering/     # Engineering & Design
├── production/      # Production Management
├── evaluation/      # Evaluation System
├── quality/         # Quality Management
├── planning/        # Planning & KPI
├── sales/           # Sales & Lifecycle
└── analytics/       # Reporting & Analytics
```

### 3. Service Layer Pattern

Complex business logic is encapsulated in service modules:

```python
# Example: QR Code Service
floor_app/operations/hr/utils/
├── qr_utils.py       # QR code generation
└── notification_utils.py  # Notification handling
```

### 4. Signal-Based Event System

Django signals for decoupled event handling:

```python
# Example: Leave Request Notifications
@receiver(post_save, sender=LeaveRequest)
def create_leave_request_notifications(sender, instance, created, **kwargs):
    # Notification logic
    pass
```

## Technology Stack

### Backend
- **Framework**: Django 5.2.6
- **Language**: Python 3.10+
- **ORM**: Django ORM
- **API**: Django REST Framework

### Database
- **Primary**: PostgreSQL 15
- **Cache**: Redis (optional)
- **Search**: PostgreSQL Full-Text Search

### Frontend
- **Framework**: Bootstrap 5
- **JavaScript**: Vanilla JS + jQuery
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js (optional)

### Infrastructure
- **Web Server**: Gunicorn + Nginx
- **Static Files**: WhiteNoise
- **Task Queue**: Celery (optional)
- **Message Broker**: Redis (optional)

### Development & Testing
- **Testing**: pytest, pytest-django
- **Linting**: flake8, black, isort
- **Coverage**: coverage.py
- **CI/CD**: GitHub Actions

## Module Architecture

### HR Module Architecture

```
hr/
├── models/
│   ├── person.py          # Person demographics
│   ├── employee.py        # Employee records
│   ├── contract.py        # Employment contracts
│   ├── shift.py           # Shift management
│   ├── asset.py           # Asset tracking
│   └── leave.py           # Leave management
├── views/
│   ├── employee_views.py
│   ├── contract_views.py
│   ├── shift_views.py
│   ├── asset_views.py
│   └── leave_views.py
├── forms/
│   └── ...
├── templates/hr/
│   ├── employees/
│   ├── contracts/
│   ├── shifts/
│   ├── assets/
│   └── leave/
├── utils/
│   ├── qr_utils.py
│   └── notification_utils.py
├── signals.py
├── admin.py
├── urls.py
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_utils.py
```

### Common Module Structure

Each module follows this standard structure:

```
module_name/
├── models/           # Database models
├── views/            # Request handlers
├── forms/            # Form definitions
├── templates/        # HTML templates
├── static/           # Module-specific static files
├── utils/            # Helper functions
├── management/       # Django commands
│   └── commands/
├── migrations/       # Database migrations
├── tests/            # Test suite
├── admin.py          # Admin interface config
├── urls.py           # URL routing
├── signals.py        # Event handlers
└── apps.py           # App configuration
```

## Database Design

### Key Design Principles

1. **Normalization**: 3NF normalized for data integrity
2. **Relationships**: Proper foreign keys and constraints
3. **Soft Deletes**: Important records use soft delete pattern
4. **Audit Fields**: Created/modified timestamps on all models
5. **Indexes**: Strategic indexes for performance

### Core Relationships

```
Person ─────1:1───── Employee ─────M:1───── Department
                         │
                         ├──────M:1───── Position
                         │
                         ├──────1:M───── Contract
                         │
                         ├──────M:M───── Shift (through ShiftAssignment)
                         │
                         ├──────M:M───── Asset (through AssetAssignment)
                         │
                         └──────1:M───── LeaveRequest

Item ────────1:M───── Stock ─────M:1───── Location
  │
  ├─────────1:M───── SerialUnit
  │
  └─────────1:M───── BOMLine ───M:1───── BOM
```

### Model Base Classes

```python
# Standard timestamp fields
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Soft delete pattern
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
```

### Database Indexes

Strategic indexes on:
- Foreign keys
- Frequently queried fields
- Search fields
- Date fields for filtering
- Unique constraints

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────┐
│          User Authentication            │
│  (Django Auth + Session Management)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Role-Based Access Control (RBAC)    │
│  ┌────────────────────────────────────┐ │
│  │  Permissions & Permission Groups   │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         View-Level Permissions          │
│  @login_required, @permission_required  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Object-Level Permissions         │
│   (Custom permission checks in views)   │
└─────────────────────────────────────────┘
```

### Security Layers

1. **Network Security**
   - SSL/TLS encryption
   - HTTPS enforcement
   - Security headers

2. **Application Security**
   - CSRF protection
   - XSS prevention
   - SQL injection prevention (ORM)
   - Secure password hashing (PBKDF2)

3. **Data Security**
   - Input validation
   - Output encoding
   - File upload restrictions
   - Rate limiting

4. **Session Security**
   - Secure session cookies
   - Session timeout
   - HTTPS-only cookies (production)

## Integration Points

### Internal Integrations

```
HR Module ←→ Employee Portal
    │
    ├──→ Inventory (Asset tracking)
    │
    └──→ Notifications

Engineering ←→ Production ←→ Inventory
    │              │
    └──────────────┴──→ Quality

Planning ←→ Production ←→ Sales
    │
    └──→ Analytics
```

### External Integration Points

1. **Email Service**
   - SMTP integration
   - Email notifications
   - Password reset

2. **File Storage**
   - Local file system
   - Cloud storage ready (S3, Azure)

3. **API Endpoints**
   - REST API via DRF
   - Authentication: Token/Session
   - Rate limiting

4. **Future Integrations**
   - ERP systems
   - IoT devices
   - Mobile apps

## Deployment Architecture

### Production Deployment

```
┌──────────────────────────────────────────────────┐
│                  Load Balancer                    │
└────────────┬─────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────┐
│                   Nginx (Reverse Proxy)           │
│  - Static file serving                            │
│  - SSL termination                                │
│  - Request routing                                │
└────────────┬─────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────┐
│            Gunicorn (WSGI Server)                 │
│  - Multiple worker processes                      │
│  - Request handling                               │
└────────────┬─────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────┐
│          Django Application                       │
│  - Business logic                                 │
│  - Template rendering                             │
│  - ORM queries                                    │
└────────────┬─────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┐
    │                 │              │
┌───▼────┐      ┌─────▼──┐     ┌────▼────┐
│PostgreSQL│     │ Redis  │     │  Files  │
│          │     │ Cache  │     │ Storage │
└──────────┘     └────────┘     └─────────┘
```

### Docker Deployment

```
docker-compose.yml defines:
- PostgreSQL container
- Redis container
- Django app container
- Nginx container

Volumes:
- Static files
- Media files
- Database data
```

### Scaling Strategy

1. **Horizontal Scaling**
   - Multiple Gunicorn workers
   - Multiple application servers
   - Load balancer distribution

2. **Database Scaling**
   - Read replicas
   - Connection pooling
   - Query optimization

3. **Caching Strategy**
   - Redis for session storage
   - Template fragment caching
   - Database query caching

4. **Static Files**
   - CDN integration
   - WhiteNoise for compression
   - Browser caching headers

## Performance Optimization

### Database Optimization

```python
# Query optimization examples

# Use select_related for ForeignKey
Employee.objects.select_related('person', 'department', 'position')

# Use prefetch_related for Many-to-Many
Employee.objects.prefetch_related('contracts', 'leave_requests')

# Only fetch needed fields
Employee.objects.values('id', 'employee_code', 'person__first_name')

# Use indexes on frequently queried fields
class Employee(models.Model):
    employee_code = models.CharField(max_length=20, db_index=True)
```

### Caching Strategy

```python
# Template fragment caching
{% cache 600 employee_sidebar employee.id %}
    ...
{% endcache %}

# View caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def employee_list(request):
    ...
```

## Monitoring & Logging

### Application Monitoring

- Error tracking: Sentry integration ready
- Performance monitoring: Django Debug Toolbar
- Log aggregation: Structured logging

### Database Monitoring

- Query performance: Django Debug Toolbar
- Slow query logging
- Connection pool monitoring

### System Metrics

- Server resources (CPU, memory, disk)
- Response times
- Request rates
- Error rates

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**System Version**: 1.0.0

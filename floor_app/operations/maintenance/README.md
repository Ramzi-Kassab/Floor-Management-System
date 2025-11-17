# Maintenance, Asset & Downtime Module

A comprehensive CMMS (Computerized Maintenance Management System) module for the Floor Management System.

## Overview

This module provides complete asset lifecycle management, preventive and corrective maintenance workflows, downtime tracking with production impact analysis, and financial loss quantification.

## Features

### 1. Asset Registry
- Complete asset lifecycle tracking (purchase to retirement)
- Hierarchical location management (Site → Building → Area → Zone)
- QR code generation for quick asset access
- Criticality-based prioritization (LOW, MEDIUM, HIGH, CRITICAL)
- Warranty tracking with expiration alerts
- Document attachments (manuals, SOPs, drawings)
- Meter reading tracking (hours, cycles, miles)
- Health score calculation

### 2. Preventive Maintenance (PM)
- Template-based PM plans with detailed instructions
- Frequency types: TIME_BASED, METER_BASED, CONDITION_BASED
- Automatic scheduling and overdue detection
- PM calendar with visual planning board
- Safety notes and required tools documentation
- Skill level requirements (BASIC, INTERMEDIATE, ADVANCED, EXPERT)
- Automatic next-due-date calculation after completion

### 3. Corrective Maintenance
- Simple request submission for operators
- Request approval workflow (NEW → UNDER_REVIEW → APPROVED → CONVERTED_TO_WO)
- Automatic conversion to work orders
- Work order lifecycle management:
  - PLANNED → ASSIGNED → IN_PROGRESS → WAITING_PARTS → COMPLETED
- Root cause analysis categories (MECHANICAL, ELECTRICAL, HYDRAULIC, etc.)
- Problem-solution documentation
- Progress notes and updates
- Parts usage tracking

### 4. Downtime & Impact Tracking
- Automatic tracking from work orders
- Manual entry for non-maintenance downtime
- Event types: UNPLANNED_BREAKDOWN, PLANNED_PM, SETUP_CHANGEOVER, etc.
- Severity classification based on duration
- Production impact quantification
- Financial loss tracking (lost vs delayed revenue)
- Lost sales confirmation workflow

### 5. Cost Management
- Labor hours and cost tracking
- Parts consumption with unit costs
- External contractor costs
- Total cost calculation (auto-computed)
- Revenue impact analysis

## Installation

The module is already integrated into the Floor Management System.

1. Add to INSTALLED_APPS in `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'floor_app.operations.maintenance.apps.MaintenanceConfig',
]
```

2. Add URL routing in `urls.py`:
```python
path("maintenance/", include(("floor_app.operations.maintenance.urls", "maintenance"), namespace="maintenance")),
```

3. Run migrations:
```bash
python manage.py makemigrations maintenance
python manage.py migrate
```

## URL Structure

```
/maintenance/
├── /                              # Main Dashboard
├── /assets/                       # Asset list with filtering
├── /assets/create/                # Create new asset
├── /assets/<code>/                # Asset detail view
├── /assets/<code>/edit/           # Edit asset
├── /qr/<token>/                   # QR code scan handler
├── /requests/                     # Maintenance request list
├── /requests/create/              # Submit new request
├── /requests/<id>/                # Request detail
├── /requests/<id>/review/         # Review/approve request
├── /requests/<id>/convert/        # Convert to work order
├── /workorders/                   # Work order list
├── /workorders/create/            # Create work order
├── /workorders/<number>/          # Work order detail
├── /workorders/<number>/edit/     # Edit work order
├── /workorders/<number>/assign/   # Assign to technician
├── /workorders/<number>/complete/ # Complete work order
├── /pm/                           # PM calendar/planning
├── /pm/templates/                 # PM template list
├── /pm/tasks/                     # PM task list
├── /pm/tasks/<id>/                # PM task detail
├── /pm/tasks/<id>/complete/       # Complete PM task
├── /downtime/                     # Downtime event list
├── /downtime/create/              # Record new downtime
├── /downtime/<id>/                # Downtime detail
├── /downtime/<id>/add-impact/     # Add production impact
├── /downtime/impact/              # Production impact report
└── /reports/                      # Reports dashboard
```

## Permissions

- `maintenance.view_asset` - View assets
- `maintenance.add_asset` - Create new assets
- `maintenance.change_asset` - Edit assets
- `maintenance.add_maintenancerequest` - Submit requests
- `maintenance.change_maintenanceworkorder` - Update work orders
- `maintenance.can_approve_request` - Approve/reject requests (custom)
- `maintenance.can_assign_workorder` - Assign technicians (custom)
- `maintenance.can_complete_workorder` - Close work orders (custom)
- `maintenance.can_record_downtime` - Log downtime events (custom)
- `maintenance.can_confirm_lost_sales` - Confirm financial impact (custom)

## Models

### Asset Registry
- **AssetCategory** - Equipment categories with default PM intervals
- **AssetLocation** - Hierarchical location structure
- **Asset** - Main asset registry with full lifecycle tracking
- **AssetDocument** - Links assets to Knowledge module documents
- **AssetMeterReading** - Historical meter readings

### Preventive Maintenance
- **PMTemplate** - Reusable PM procedure templates
- **PMSchedule** - Asset-specific PM schedules
- **PMTask** - Individual PM task execution records

### Work Orders
- **MaintenanceRequest** - User-submitted maintenance requests
- **MaintenanceWorkOrder** - Complete work order lifecycle
- **WorkOrderNote** - Progress notes and updates
- **WorkOrderPart** - Parts consumption tracking

### Downtime & Impact
- **DowntimeEvent** - Downtime/stoppage events
- **ProductionImpact** - Links downtime to production batches
- **LostSalesRecord** - Confirmed financial losses

## Integration Points

- **HR Module**: Employee assignment, department ownership
- **Knowledge Module**: Document and procedure linking
- **Future Inventory Module**: Parts consumption tracking (prepared with nullable FKs)
- **Future Production Module**: Batch and job card linking (prepared with nullable FKs)

## Services

### MaintenanceService
- `get_dashboard_stats()` - Key metrics for dashboard
- `get_assets_by_status()` - Asset distribution charts
- `get_work_orders_by_type()` - Work order type breakdown
- `convert_request_to_work_order()` - Request conversion logic
- `generate_pm_tasks()` - Automatic PM task generation

### DowntimeService
- `get_downtime_summary()` - Downtime statistics
- `get_downtime_by_reason()` - Breakdown by cause
- `get_production_impact_summary()` - Financial impact analysis
- `get_top_downtime_assets()` - Worst performing assets

### AssetService
- `get_asset_health_score()` - Health scoring algorithm
- `get_warranty_expiring_assets()` - Warranty alerts
- `generate_qr_token()` - QR code generation

## Admin Interface

Full Django admin integration with:
- Custom badges for status and priority
- Inline editing for related models
- Autocomplete fields for foreign keys
- Fieldsets for organized form layout
- Search, filtering, and list editing

## Templates

Complete Bootstrap 5 frontend with:
- Responsive dashboard with statistics cards
- Asset list with advanced filtering
- Asset detail with health score visualization
- PM calendar with overdue/upcoming views
- Work order board with status tracking
- Request approval workflow
- Downtime event recording
- Production impact analysis reports
- Mobile-friendly responsive design

## Signals

Automatic actions:
- Update asset status when work order status changes
- Update PM schedule when task is completed
- Calculate total cost before saving work order
- Update parts cost when parts are added

## Usage Examples

### Creating an Asset
```python
from floor_app.operations.maintenance.models import Asset, AssetCategory

category = AssetCategory.objects.create(
    code='GRN',
    name='Grinder',
    default_criticality='HIGH'
)

asset = Asset.objects.create(
    asset_code='GRN-001',
    name='Surface Grinder #1',
    category=category,
    status='IN_SERVICE',
    criticality='HIGH',
    manufacturer='Okamoto',
    model_number='ACC-12-24DX',
    serial_number='SN123456'
)
```

### Recording Downtime with Impact
```python
from floor_app.operations.maintenance.models import DowntimeEvent, ProductionImpact
from django.utils import timezone

event = DowntimeEvent.objects.create(
    asset=asset,
    event_type='UNPLANNED_BREAKDOWN',
    start_time=timezone.now(),
    is_planned=False,
    reason_category='MECHANICAL',
    reason_description='Spindle bearing failure',
    has_production_impact=True
)

impact = ProductionImpact.objects.create(
    downtime_event=event,
    impact_type='BATCH',
    batch_reference='BATCH-2025-001',
    customer_name='Customer ABC',
    delay_minutes=480,
    lost_or_delayed_revenue=50000.00,
    currency='SAR'
)
```

## File Structure

```
maintenance/
├── __init__.py
├── apps.py                    # App configuration
├── admin.py                   # Admin interface (263 lines)
├── forms.py                   # All forms (400+ lines)
├── models/
│   ├── __init__.py           # Model imports
│   ├── asset.py              # Asset registry models
│   ├── preventive.py         # PM models
│   ├── workorder.py          # Work order models
│   └── downtime.py           # Downtime tracking models
├── services.py               # Business logic services
├── signals.py                # Django signals
├── urls.py                   # URL routing
├── views.py                  # View functions (700+ lines)
├── migrations/
│   └── __init__.py
├── templates/
│   └── maintenance/
│       ├── dashboard.html
│       ├── asset_list.html
│       ├── asset_detail.html
│       ├── asset_form.html
│       ├── request_list.html
│       ├── request_form.html
│       ├── request_detail.html
│       ├── request_review.html
│       ├── workorder_list.html
│       ├── workorder_detail.html
│       ├── workorder_form.html
│       ├── workorder_assign.html
│       ├── workorder_complete.html
│       ├── pm_calendar.html
│       ├── pm_task_list.html
│       ├── pm_task_detail.html
│       ├── pm_task_complete.html
│       ├── pm_template_list.html
│       ├── downtime_list.html
│       ├── downtime_detail.html
│       ├── downtime_form.html
│       ├── production_impact_form.html
│       ├── downtime_impact.html
│       └── reports_dashboard.html
├── MAINTENANCE_DESIGN.md     # Schema design document
└── README.md                 # This file
```

## Next Steps

1. Run migrations to create database tables
2. Create sample data through admin
3. Configure user permissions
4. Customize PM templates for your equipment
5. Set up asset categories and locations
6. Train users on request submission workflow

## Contributing

This module follows the project's coding standards:
- PEP 8 style guidelines
- Django best practices
- DRY (Don't Repeat Yourself)
- Comprehensive documentation
- Type hints where applicable

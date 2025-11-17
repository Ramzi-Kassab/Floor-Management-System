# Maintenance & Asset Management Module

## Overview

A comprehensive CMMS (Computerized Maintenance Management System) module for the Floor Management System, designed to manage factory equipment, preventive maintenance, corrective work orders, downtime tracking, and financial impact analysis.

## Features

### 1. Asset Registry
- Complete equipment/machine master database
- Hierarchical categories and locations
- Status and criticality tracking
- QR code generation for quick access
- Document attachment (manuals, drawings, SOPs)
- Warranty and financial information

### 2. Preventive Maintenance (PM)
- PM plan templates with detailed instructions
- Time-based and meter-based scheduling
- Automatic task generation
- Calendar view for planning
- Task execution tracking

### 3. Corrective Maintenance
- Maintenance request workflow (operators → planners)
- Work order management
- Root cause analysis
- Priority and status tracking
- Parts usage recording

### 4. Downtime & Impact Tracking
- Equipment downtime recording
- Production impact linking (batches, job cards)
- Lost/delayed revenue tracking
- Severity scoring
- Verification workflow

## Installation

The module is automatically registered in Django settings. After pulling the code:

```bash
# Apply migrations
python manage.py makemigrations maintenance
python manage.py migrate

# Create superuser (if needed)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## URL Structure

All maintenance URLs are under `/maintenance/`:

- `/maintenance/` - Dashboard
- `/maintenance/assets/` - Asset registry
- `/maintenance/requests/` - Maintenance requests
- `/maintenance/work-orders/` - Work orders
- `/maintenance/pm/tasks/` - PM tasks
- `/maintenance/pm/calendar/` - PM calendar
- `/maintenance/downtime/` - Downtime events
- `/maintenance/settings/` - Configuration

## Usage Guide

### Adding an Asset

1. Navigate to **Maintenance → Assets**
2. Click **"Add Asset"**
3. Fill in required fields:
   - Asset Code (unique identifier)
   - Name
   - Category
   - Location
   - Status & Criticality
4. Add optional information (manufacturer, serial number, etc.)
5. Click **"Create Asset"**

### Creating a Maintenance Request

Operators/supervisors can report issues:

1. Navigate to **Maintenance → Requests → New Request**
2. Select the affected asset
3. Describe the problem
4. Set priority (Critical if production stopped)
5. Submit request

Planners will review and convert to work orders.

### Managing Work Orders

1. **Create**: From approved requests or directly
2. **Assign**: To maintenance technicians
3. **Start**: When work begins
4. **Complete**: Log solution, root cause, parts used
5. **Follow-up**: Create additional WOs if needed

### Recording Downtime

1. Navigate to **Maintenance → Downtime → Create**
2. Select asset
3. Record start time (and end time if known)
4. Classify as planned/unplanned
5. Select reason category
6. Mark if production was affected

### PM Scheduling

1. Create **PM Plans** with:
   - Tasks to perform
   - Safety instructions
   - Tools required
   - Frequency (daily, weekly, monthly, etc.)
2. Assign plans to assets or categories
3. System generates **PM Schedules** automatically
4. **PM Tasks** are created when due

## Data Models

### Core Models

| Model | Purpose |
|-------|---------|
| AssetCategory | Equipment types (Grinder, Oven, etc.) |
| AssetLocation | Physical locations (Site → Area → Zone) |
| Asset | Individual equipment records |
| AssetDocument | Attached files (manuals, drawings) |

### PM Models

| Model | Purpose |
|-------|---------|
| PMPlan | Template for preventive maintenance |
| PMSchedule | Asset-specific PM schedules |
| PMTask | Individual PM task instances |

### Corrective Models

| Model | Purpose |
|-------|---------|
| MaintenanceRequest | User-submitted maintenance requests |
| WorkOrder | Actual maintenance work |
| WorkOrderAttachment | Files attached to work orders |
| PartsUsage | Spare parts consumed |

### Downtime Models

| Model | Purpose |
|-------|---------|
| DowntimeEvent | Equipment unavailability records |
| ProductionImpact | Link to affected production jobs |
| LostSales | Financial impact tracking |

## API Endpoints

JSON endpoints for integration:

- `GET /maintenance/api/stats/` - Dashboard statistics

## Key Features

### Auto-Generated Numbers
- Asset Code: `AST-{UUID}`
- Request Number: `REQ-YYYY-NNNN`
- Work Order Number: `WO-YYYY-NNNN`
- PM Task Number: `PMT-YYYY-NNNN`

### QR Code Integration
Each asset has a unique QR token. When scanned:
- Opens asset detail page
- Quick actions for requests and downtime
- Links to open work orders

### Root Cause Analysis
Work orders support root cause tracking:
- MECHANICAL, ELECTRICAL, HYDRAULIC
- PNEUMATIC, CONTROL/SOFTWARE, WEAR
- MISUSE, SAFETY_EVENT, UTILITY
- CALIBRATION, CONTAMINATION, OTHER

### Financial Tracking
- Parts cost per work order
- Labor cost tracking
- Lost/delayed revenue recording
- Cost analysis per asset

## Permissions

Roles and access:

| Action | Operator | Technician | Planner | Manager |
|--------|----------|------------|---------|---------|
| View Assets | Yes | Yes | Yes | Yes |
| Create Request | Yes | Yes | Yes | Yes |
| Approve Request | No | No | Yes | Yes |
| Start Work Order | No | Yes | Yes | No |
| Complete Work Order | No | Yes | Yes | No |
| View Reports | No | No | Yes | Yes |

## Integration Points

### With Production Module
- Link downtime to BatchOrder, JobCard
- Track production delays
- Impact on delivery schedules

### With Inventory Module
- Record parts usage (item IDs)
- Track maintenance costs
- Stock deduction (future)

### With HR Module
- Assign technicians (employee references)
- Track who performed maintenance
- Responsibility tracking

### With QR Codes Module
- Asset QR token generation
- Quick scan access to actions
- Audit trail for scans

## Dashboard Metrics

The main dashboard displays:

- Total assets and status breakdown
- Open work orders count
- Overdue PM tasks
- Total downtime hours (monthly)
- Pending maintenance requests
- Lost sales/revenue impact
- Top 5 assets by downtime
- Recent work orders

## Templates

Key templates included:

- Dashboard with statistics
- Asset list with filters
- Asset detail with tabs
- Work order management
- Request workflow
- PM task tracking

## Future Enhancements

1. **Automatic PM Task Generation**: Daily job to create tasks from schedules
2. **Email Notifications**: Alerts for overdue PMs and critical breakdowns
3. **Mobile-Optimized Views**: Dedicated mobile interface for technicians
4. **Advanced Reporting**: PDF reports, trend analysis
5. **Predictive Maintenance**: ML-based failure prediction
6. **Vendor Management**: External service provider tracking
7. **Budget Planning**: Maintenance cost forecasting

## Database Tables

All tables prefixed with `maintenance_`:

- `maintenance_asset_category`
- `maintenance_asset_location`
- `maintenance_asset`
- `maintenance_asset_document`
- `maintenance_pm_plan`
- `maintenance_pm_schedule`
- `maintenance_pm_task`
- `maintenance_request`
- `maintenance_work_order`
- `maintenance_wo_attachment`
- `maintenance_downtime_event`
- `maintenance_production_impact`
- `maintenance_lost_sales`
- `maintenance_parts_usage`

## Support

For issues or questions:
1. Check Django admin at `/admin/`
2. Review model definitions in `models/` directory
3. Consult the design document `MAINTENANCE_DESIGN.md`

## Files Structure

```
maintenance/
├── __init__.py
├── apps.py
├── admin/
│   ├── __init__.py
│   ├── asset.py
│   ├── preventive.py
│   ├── corrective.py
│   └── downtime.py
├── models/
│   ├── __init__.py
│   ├── asset.py
│   ├── preventive.py
│   ├── corrective.py
│   ├── downtime.py
│   └── parts.py
├── forms.py
├── views.py
├── urls.py
├── signals.py
├── migrations/
├── templates/maintenance/
│   ├── dashboard.html
│   ├── asset/
│   ├── corrective/
│   ├── preventive/
│   ├── downtime/
│   └── settings/
├── MAINTENANCE_DESIGN.md
└── README.md
```

---

**Module Version**: 1.0.0
**Created**: November 2025
**Author**: Claude Code Agent
**Compatible with**: Django 5.2, PostgreSQL

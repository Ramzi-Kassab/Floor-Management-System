# Maintenance, Asset & Downtime Module - Design Document

## Overview

A comprehensive CMMS (Computerized Maintenance Management System) module for the Floor Management System, designed for PDC bit manufacturing and repair operations.

## Core Entities

### 1. Asset Registry

```
AssetCategory
├── name (Grinder, Oven, Brazing Station, etc.)
├── description
├── default_criticality
└── icon

AssetLocation
├── name (PDC Workshop, RC Area, Matrix Infiltration)
├── code
├── parent (hierarchical: Site → Building → Area → Zone)
├── description
└── is_active

Asset
├── asset_code (internal tag: "GRN-001", "OVN-002")
├── name
├── category_id → AssetCategory
├── location_id → AssetLocation
├── status (IN_SERVICE, UNDER_MAINTENANCE, OUT_OF_SERVICE, SCRAPPED)
├── criticality (LOW, MEDIUM, HIGH, CRITICAL)
├── manufacturer, model, serial_number
├── purchase_date, warranty_expires
├── erp_asset_number (external system reference)
├── qr_token (for QR code scanning)
├── notes, specifications (JSON)
└── AuditMixin, SoftDeleteMixin, PublicIdMixin

AssetDocument
├── asset_id → Asset
├── document_id → Document (from knowledge module)
├── document_type (MANUAL, OEM_GUIDE, SOP, DRAWING, WARRANTY)
└── description
```

### 2. Preventive Maintenance

```
PMTemplate
├── code (template identifier)
├── name
├── description
├── instructions (rich text)
├── safety_notes
├── tools_required
├── estimated_duration_minutes
├── frequency_type (TIME_BASED, METER_BASED, CONDITION_BASED)
├── frequency_days (e.g., 30, 90, 180, 365)
├── frequency_hours (for meter-based)
├── applies_to_category_id → AssetCategory (optional)
├── skill_level_required
└── is_active

PMSchedule
├── asset_id → Asset
├── pm_template_id → PMTemplate
├── last_performed_at
├── next_due_date
├── meter_reading_at_last_pm
├── next_due_meter_reading
├── is_overdue
└── auto_generated (system vs manual)

PMTask (actual execution of scheduled PM)
├── schedule_id → PMSchedule
├── status (SCHEDULED, IN_PROGRESS, COMPLETED, SKIPPED, OVERDUE)
├── scheduled_date
├── actual_start, actual_end
├── performed_by_id → HREmployee
├── duration_minutes
├── notes, findings
├── next_due_updated
└── work_order_id → MaintenanceWorkOrder (if generates WO)
```

### 3. Maintenance Requests & Work Orders

```
MaintenanceRequest
├── request_number (auto-generated)
├── asset_id → Asset
├── title
├── description (symptoms/problem)
├── priority (LOW, MEDIUM, HIGH, CRITICAL)
├── requested_by_id → User
├── department_id → Department
├── status (NEW, UNDER_REVIEW, APPROVED, REJECTED, CONVERTED_TO_WO)
├── reviewed_by_id → User
├── reviewed_at
├── rejection_reason
├── converted_work_order_id → MaintenanceWorkOrder
└── attachments (photos of problem)

MaintenanceWorkOrder
├── work_order_number (auto-generated)
├── asset_id → Asset
├── title
├── description
├── work_order_type (PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION)
├── priority (LOW, MEDIUM, HIGH, CRITICAL)
├── status (PLANNED, ASSIGNED, IN_PROGRESS, WAITING_PARTS, WAITING_VENDOR, ON_HOLD, COMPLETED, CANCELLED)
├── planned_start, planned_end
├── actual_start, actual_end
├── assigned_to_id → HREmployee
├── assigned_team (JSON list of employee IDs)
├── source_request_id → MaintenanceRequest (if from request)
├── source_pm_task_id → PMTask (if from PM)
├── root_cause_category (MECHANICAL, ELECTRICAL, HYDRAULIC, PNEUMATIC, CONTROL_SOFTWARE, WEAR, MISUSE, SAFETY_EVENT, UTILITY, OTHER)
├── root_cause_detail (free text)
├── problem_description
├── solution_summary
├── failure_mode
├── total_cost (calculated from parts + labor)
├── labor_hours
└── attachments

WorkOrderNote (comments/updates)
├── work_order_id → MaintenanceWorkOrder
├── note_type (PROGRESS, ISSUE, RESOLUTION, GENERAL)
├── content
├── created_by_id → User
└── created_at
```

### 4. Downtime & Impact Tracking

```
DowntimeEvent
├── asset_id → Asset
├── work_order_id → MaintenanceWorkOrder (optional)
├── event_type (UNPLANNED_BREAKDOWN, PLANNED_PM, SETUP_CHANGEOVER, WAITING_PARTS, UTILITY_FAILURE)
├── start_time, end_time
├── duration_minutes (computed or stored)
├── is_planned
├── reason_category (same as root_cause_category)
├── reason_description
├── reported_by_id → User
├── severity (MINOR, MODERATE, MAJOR, CRITICAL)
└── notes

ProductionImpact (links downtime to production)
├── downtime_event_id → DowntimeEvent
├── impact_type (BATCH, JOB_CARD, OPERATION)
├── batch_id (FK to future Batch model, nullable for now)
├── job_card_id (FK to future JobCard model, nullable for now)
├── operation_id (FK to future Operation model, nullable for now)
├── customer_name (text for now, FK later)
├── expected_completion_date
├── actual_completion_date
├── delay_minutes
├── lost_or_delayed_revenue (Decimal)
├── currency (default 'SAR')
├── is_revenue_confirmed
├── impact_description
└── notes

LostSalesRecord (financial impact summary)
├── production_impact_id → ProductionImpact
├── customer_name
├── order_reference
├── original_value
├── revenue_lost
├── revenue_delayed
├── recovery_possible
├── confirmed_by_id → User
├── confirmed_at
└── notes
```

### 5. Parts & Inventory Integration

```
WorkOrderPart (parts consumed)
├── work_order_id → MaintenanceWorkOrder
├── part_number (text for now, FK to Item later)
├── part_description
├── quantity_used
├── unit_cost
├── total_cost (computed)
├── warehouse_location (text for now)
├── inventory_transaction_id (FK to future transaction)
└── notes

SparePartRecommendation (suggested spares per asset)
├── asset_id → Asset
├── part_number
├── part_description
├── minimum_quantity
├── reorder_point
└── typical_usage_per_year
```

## Key Features

1. **Asset Lifecycle Management**
   - Track from purchase to retirement
   - QR code for quick access
   - Document attachments (manuals, SOPs)
   - Criticality-based prioritization

2. **Preventive Maintenance**
   - Template-based PM plans
   - Time-based and meter-based scheduling
   - Calendar view of upcoming tasks
   - Overdue alerts

3. **Corrective Maintenance**
   - Simple request submission (operators)
   - Request approval workflow
   - Work order management with full lifecycle
   - Root cause analysis

4. **Downtime Analytics**
   - Automatic tracking from work orders
   - Manual entry for non-maintenance downtime
   - Production impact quantification
   - Financial loss tracking

5. **QR Integration**
   - Scan asset QR → view details / create request
   - Quick actions from mobile

## Integration Points

- **HR Module**: Employees assigned to work orders, requesters
- **Knowledge Module**: Link SOPs and procedures to PM templates
- **Future Inventory**: Parts consumption tracking
- **Future Production**: Link downtime to batches/jobs

## URLs Structure

```
/maintenance/
├── /                          # Dashboard
├── /assets/                   # Asset list
├── /assets/<code>/           # Asset detail
├── /assets/create/           # New asset
├── /pm/                      # PM calendar/list
├── /pm/templates/            # PM templates
├── /pm/<id>/                 # PM task detail
├── /requests/                # Maintenance requests
├── /requests/create/         # New request
├── /requests/<id>/           # Request detail
├── /workorders/              # Work orders
├── /workorders/<number>/     # WO detail
├── /downtime/                # Downtime events
├── /downtime/impact/         # Production impact
├── /reports/                 # Reports dashboard
└── /qr/<token>/              # QR scan handler
```

## Permissions

- `maintenance.view_asset` - View assets
- `maintenance.add_maintenancerequest` - Create requests
- `maintenance.change_maintenanceworkorder` - Update work orders
- `maintenance.can_approve_request` - Approve/reject requests
- `maintenance.can_assign_workorder` - Assign technicians
- `maintenance.can_complete_workorder` - Close work orders
- `maintenance.can_record_downtime` - Log downtime events
- `maintenance.can_confirm_lost_sales` - Confirm financial impact

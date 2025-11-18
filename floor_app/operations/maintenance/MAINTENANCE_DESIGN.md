# Maintenance & Asset Management Module - Design Document

**Date:** November 17, 2025
**Status:** Design Complete - Ready for Implementation
**Module Path:** `floor_app/operations/maintenance/`

---

## 1. Executive Summary

This document outlines the design for a comprehensive Maintenance/CMMS (Computerized Maintenance Management System) module integrated into the Floor Management System. The module handles:

- Asset & Equipment Registry
- Preventive Maintenance (PM) Planning & Scheduling
- Corrective Maintenance & Work Orders
- Downtime Tracking with Production Impact
- Lost Sales/Revenue Recording
- Spare Parts Usage Tracking
- QR Code Integration for Quick Access

---

## 2. Module Architecture

### Directory Structure

```
floor_app/operations/maintenance/
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
│   ├── asset.py           # Asset, AssetCategory, AssetLocation
│   ├── preventive.py      # PMPlan, PMSchedule, PMTask
│   ├── corrective.py      # MaintenanceRequest, WorkOrder
│   ├── downtime.py        # DowntimeEvent, ProductionImpact, LostSales
│   └── parts.py           # PartsUsage
├── forms.py
├── views.py
├── urls.py
├── signals.py
├── services.py            # Business logic
├── migrations/
│   └── __init__.py
├── templates/maintenance/
│   ├── dashboard.html
│   ├── asset/
│   ├── preventive/
│   ├── corrective/
│   └── downtime/
├── fixtures/
│   └── initial_data.json
├── README.md
└── tests.py
```

---

## 3. Data Model Design

### 3.1 Asset & Equipment Registry

#### AssetCategory
```python
class AssetCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Categories for grouping assets (e.g., Grinder, Oven, Compressor).
    Used for filtering, PM templates, and reporting.
    """

    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=100)
    description = TextField(blank=True)
    parent = ForeignKey('self', null=True, blank=True)  # Hierarchy support

    # PM defaults
    default_pm_interval_days = PositiveIntegerField(null=True, blank=True)
    requires_certification = BooleanField(default=False)

    class Meta:
        db_table = "maintenance_asset_category"
```

#### AssetLocation
```python
class AssetLocation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Hierarchical locations (Site → Area → Zone).
    Examples: PDC Workshop, Roller Cone Area, Matrix Infiltration, NDT Room.
    """

    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=150)
    parent = ForeignKey('self', null=True, blank=True)  # Hierarchy
    description = TextField(blank=True)

    # Contact info for location
    responsible_person = ForeignKey(HREmployee, null=True, blank=True)

    class Meta:
        db_table = "maintenance_asset_location"
```

#### Asset
```python
class Asset(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Central asset registry - the main equipment/machine master.
    """

    STATUS_CHOICES = (
        ('IN_SERVICE', 'In Service'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('SCRAPPED', 'Scrapped'),
    )

    CRITICALITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    # Identification
    asset_code = CharField(max_length=50, unique=True)  # Internal tag
    name = CharField(max_length=200)
    description = TextField(blank=True)

    # Classification
    category = ForeignKey(AssetCategory)
    location = ForeignKey(AssetLocation)
    parent_asset = ForeignKey('self', null=True, blank=True)  # Sub-equipment

    # Manufacturer info
    manufacturer = CharField(max_length=150, blank=True)
    model_number = CharField(max_length=100, blank=True)
    serial_number = CharField(max_length=100, blank=True)

    # Status & Criticality
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='IN_SERVICE')
    criticality = CharField(max_length=10, choices=CRITICALITY_CHOICES, default='MEDIUM')
    is_critical_production_asset = BooleanField(default=False)

    # Dates
    installation_date = DateField(null=True, blank=True)
    warranty_expiry_date = DateField(null=True, blank=True)
    last_maintenance_date = DateField(null=True, blank=True)

    # ERP Integration
    erp_asset_number = CharField(max_length=100, blank=True)

    # QR/Barcode
    qr_token = CharField(max_length=100, unique=True, blank=True)

    # Costs
    purchase_cost = DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    replacement_cost = DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Meters (for meter-based PM)
    current_meter_reading = DecimalField(max_digits=12, decimal_places=2, default=0)
    meter_unit = CharField(max_length=50, blank=True)  # hours, cycles, km

    class Meta:
        db_table = "maintenance_asset"
        indexes = [
            Index(fields=['asset_code']),
            Index(fields=['status', 'criticality']),
            Index(fields=['category', 'location']),
            Index(fields=['qr_token']),
        ]
```

#### AssetDocument
```python
class AssetDocument(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Documents attached to assets (manuals, drawings, SOPs, OEM guides).
    """

    DOC_TYPE_CHOICES = (
        ('MANUAL', 'User Manual'),
        ('DRAWING', 'Technical Drawing'),
        ('SOP', 'Standard Operating Procedure'),
        ('WARRANTY', 'Warranty Document'),
        ('CERTIFICATE', 'Certificate'),
        ('PHOTO', 'Photo'),
        ('OTHER', 'Other'),
    )

    asset = ForeignKey(Asset)
    title = CharField(max_length=200)
    doc_type = CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    file = FileField(upload_to='maintenance/asset_docs/')
    description = TextField(blank=True)

    class Meta:
        db_table = "maintenance_asset_document"
```

---

### 3.2 Preventive Maintenance (PM)

#### PMPlan (Template)
```python
class PMPlan(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    PM Plan/Template defining what maintenance to do and how often.
    Can apply to specific assets or asset categories.
    """

    FREQUENCY_TYPE_CHOICES = (
        ('TIME_BASED', 'Time Based'),
        ('METER_BASED', 'Meter Based'),
        ('CONDITION_BASED', 'Condition Based'),
    )

    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    description = TextField()

    # What to do
    tasks_description = TextField(help_text="Detailed steps to perform")
    safety_instructions = TextField(blank=True)
    tools_required = TextField(blank=True)

    # Who
    required_skill_level = CharField(max_length=50, blank=True)

    # Time
    estimated_duration_minutes = PositiveIntegerField(default=60)

    # Frequency
    frequency_type = CharField(max_length=20, choices=FREQUENCY_TYPE_CHOICES, default='TIME_BASED')
    interval_days = PositiveIntegerField(null=True, blank=True)  # For time-based
    interval_meter_value = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Scope
    applies_to_category = ForeignKey(AssetCategory, null=True, blank=True)
    applies_to_specific_assets = ManyToManyField(Asset, blank=True)

    # Active control
    is_active = BooleanField(default=True)

    class Meta:
        db_table = "maintenance_pm_plan"
```

#### PMSchedule
```python
class PMSchedule(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Specific PM schedule for an asset based on a plan.
    Tracks when PM is due for each asset.
    """

    asset = ForeignKey(Asset)
    pm_plan = ForeignKey(PMPlan)

    # Schedule
    next_due_date = DateField()
    last_completed_date = DateField(null=True, blank=True)

    # For meter-based
    next_due_meter_reading = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    is_active = BooleanField(default=True)

    class Meta:
        db_table = "maintenance_pm_schedule"
        unique_together = [['asset', 'pm_plan']]
```

#### PMTask (Execution Instance)
```python
class PMTask(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Actual PM task instance - the work to be done.
    Generated from PMSchedule when due.
    """

    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('OVERDUE', 'Overdue'),
    )

    schedule = ForeignKey(PMSchedule)

    # Task info
    task_number = CharField(max_length=50, unique=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    # Timing
    scheduled_date = DateField()
    actual_start = DateTimeField(null=True, blank=True)
    actual_end = DateTimeField(null=True, blank=True)
    actual_duration_minutes = PositiveIntegerField(null=True, blank=True)

    # Assignment
    assigned_to = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    performed_by = ForeignKey(HREmployee, null=True, blank=True)

    # Results
    completion_notes = TextField(blank=True)
    issues_found = TextField(blank=True)
    follow_up_required = BooleanField(default=False)

    # Meter reading at completion
    meter_reading_at_completion = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "maintenance_pm_task"
        indexes = [
            Index(fields=['task_number']),
            Index(fields=['status', 'scheduled_date']),
        ]
```

---

### 3.3 Corrective Maintenance

#### MaintenanceRequest
```python
class MaintenanceRequest(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Request from operators/supervisors for maintenance.
    Simple form to report issues.
    """

    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to Work Order'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    request_number = CharField(max_length=50, unique=True)
    asset = ForeignKey(Asset)

    # Request details
    title = CharField(max_length=200)
    description = TextField()
    symptoms = TextField(blank=True)
    priority = CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')

    # Requester
    requested_by = ForeignKey(settings.AUTH_USER_MODEL, related_name='maintenance_requests')
    request_date = DateTimeField(auto_now_add=True)

    # Status
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    reviewed_by = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='requests_reviewed')
    reviewed_at = DateTimeField(null=True, blank=True)
    rejection_reason = TextField(blank=True)

    # Resulting work order
    work_order = ForeignKey('WorkOrder', null=True, blank=True, related_name='source_request')

    class Meta:
        db_table = "maintenance_request"
        indexes = [
            Index(fields=['request_number']),
            Index(fields=['status', 'priority']),
            Index(fields=['asset', 'status']),
        ]
```

#### WorkOrder
```python
class WorkOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Main work order - the job executed by maintenance team.
    Can be created from PM tasks, requests, or directly.
    """

    STATUS_CHOICES = (
        ('PLANNED', 'Planned'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_PARTS', 'Waiting for Parts'),
        ('WAITING_VENDOR', 'Waiting for Vendor'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    TYPE_CHOICES = (
        ('CORRECTIVE', 'Corrective'),
        ('PREVENTIVE', 'Preventive'),
        ('EMERGENCY', 'Emergency'),
        ('IMPROVEMENT', 'Improvement'),
    )

    ROOT_CAUSE_CHOICES = (
        ('MECHANICAL', 'Mechanical Failure'),
        ('ELECTRICAL', 'Electrical Failure'),
        ('HYDRAULIC', 'Hydraulic Issue'),
        ('PNEUMATIC', 'Pneumatic Issue'),
        ('CONTROL_SOFTWARE', 'Control/Software'),
        ('WEAR', 'Normal Wear'),
        ('MISUSE', 'Operator Misuse'),
        ('SAFETY_EVENT', 'Safety Event'),
        ('UTILITY', 'Utility (Power/Air/Water)'),
        ('OTHER', 'Other'),
    )

    # Identification
    wo_number = CharField(max_length=50, unique=True)
    asset = ForeignKey(Asset)

    # Classification
    wo_type = CharField(max_length=20, choices=TYPE_CHOICES, default='CORRECTIVE')
    priority = CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')

    # Problem description
    title = CharField(max_length=200)
    problem_description = TextField()

    # Planning
    planned_start = DateTimeField(null=True, blank=True)
    planned_end = DateTimeField(null=True, blank=True)
    estimated_duration_minutes = PositiveIntegerField(null=True, blank=True)

    # Execution
    actual_start = DateTimeField(null=True, blank=True)
    actual_end = DateTimeField(null=True, blank=True)
    actual_duration_minutes = PositiveIntegerField(null=True, blank=True)

    # Assignment
    assigned_to = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='assigned_work_orders')
    team_members = ManyToManyField(HREmployee, blank=True, related_name='work_order_team')

    # Root Cause Analysis
    root_cause_category = CharField(max_length=20, choices=ROOT_CAUSE_CHOICES, blank=True)
    root_cause_detail = TextField(blank=True)

    # Solution
    solution_summary = TextField(blank=True)
    actions_taken = TextField(blank=True)

    # Follow-up
    follow_up_required = BooleanField(default=False)
    follow_up_notes = TextField(blank=True)

    # Source
    source_pm_task = ForeignKey(PMTask, null=True, blank=True)
    source_request = ForeignKey(MaintenanceRequest, null=True, blank=True)

    # Costs
    labor_cost = DecimalField(max_digits=12, decimal_places=2, default=0)
    parts_cost = DecimalField(max_digits=12, decimal_places=2, default=0)
    external_cost = DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "maintenance_work_order"
        indexes = [
            Index(fields=['wo_number']),
            Index(fields=['status', 'priority']),
            Index(fields=['asset', 'status']),
            Index(fields=['wo_type', 'status']),
        ]
```

#### WorkOrderAttachment
```python
class WorkOrderAttachment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Files attached to work orders (photos of defects, reports, etc.)
    """

    work_order = ForeignKey(WorkOrder)
    title = CharField(max_length=200)
    file = FileField(upload_to='maintenance/wo_attachments/')
    description = TextField(blank=True)

    class Meta:
        db_table = "maintenance_wo_attachment"
```

---

### 3.4 Downtime & Production Impact

#### DowntimeEvent
```python
class DowntimeEvent(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Records of asset downtime - when equipment was not available.
    """

    DOWNTIME_TYPE_CHOICES = (
        ('PLANNED', 'Planned (PM)'),
        ('UNPLANNED', 'Unplanned (Breakdown)'),
    )

    REASON_CATEGORY_CHOICES = (
        ('BREAKDOWN', 'Breakdown'),
        ('PM_SCHEDULED', 'Scheduled PM'),
        ('SETUP', 'Setup/Changeover'),
        ('NO_OPERATOR', 'No Operator'),
        ('NO_MATERIAL', 'No Material'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('UTILITY_FAILURE', 'Utility Failure'),
        ('OTHER', 'Other'),
    )

    asset = ForeignKey(Asset)
    work_order = ForeignKey(WorkOrder, null=True, blank=True)

    # Timing
    start_time = DateTimeField()
    end_time = DateTimeField(null=True, blank=True)
    duration_minutes = PositiveIntegerField(null=True, blank=True)  # Calculated or manual

    # Classification
    downtime_type = CharField(max_length=20, choices=DOWNTIME_TYPE_CHOICES)
    reason_category = CharField(max_length=20, choices=REASON_CATEGORY_CHOICES)
    reason_detail = TextField(blank=True)

    # Impact assessment
    production_affected = BooleanField(default=False)

    class Meta:
        db_table = "maintenance_downtime_event"
        indexes = [
            Index(fields=['asset', 'start_time']),
            Index(fields=['downtime_type', 'reason_category']),
            Index(fields=['start_time', 'end_time']),
        ]
```

#### ProductionImpact
```python
class ProductionImpact(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Links downtime to specific production jobs/batches affected.
    """

    downtime_event = ForeignKey(DowntimeEvent)

    # Production references (using GenericForeignKey pattern or direct FKs)
    # We'll use direct FKs for now, assuming these models exist
    batch_order_id = BigIntegerField(null=True, blank=True)  # Reference to production.BatchOrder
    job_card_id = BigIntegerField(null=True, blank=True)     # Reference to production.JobCard

    # Impact details
    delay_minutes = PositiveIntegerField(default=0)
    planned_completion = DateTimeField(null=True, blank=True)
    actual_completion = DateTimeField(null=True, blank=True)
    impact_description = TextField(blank=True)

    class Meta:
        db_table = "maintenance_production_impact"
```

#### LostSales
```python
class LostSales(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Records financial impact of downtime - lost or delayed revenue.
    """

    IMPACT_TYPE_CHOICES = (
        ('LOST', 'Lost Sale (Cancelled)'),
        ('DELAYED', 'Delayed Delivery'),
        ('PENALTY', 'Late Delivery Penalty'),
        ('REWORK', 'Rework Cost'),
    )

    downtime_event = ForeignKey(DowntimeEvent, null=True, blank=True)
    production_impact = ForeignKey(ProductionImpact, null=True, blank=True)

    # Reference
    batch_order_id = BigIntegerField(null=True, blank=True)
    customer_name = CharField(max_length=200, blank=True)

    # Financial impact
    impact_type = CharField(max_length=20, choices=IMPACT_TYPE_CHOICES)
    expected_delivery_date = DateField(null=True, blank=True)
    actual_delivery_date = DateField(null=True, blank=True)

    # Revenue
    lost_or_delayed_revenue = DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = CharField(max_length=3, default='SAR')
    is_confirmed = BooleanField(default=False)  # Rough estimate vs confirmed

    notes = TextField(blank=True)

    class Meta:
        db_table = "maintenance_lost_sales"
        indexes = [
            Index(fields=['impact_type']),
            Index(fields=['is_confirmed']),
        ]
```

---

### 3.5 Parts Usage

#### PartsUsage
```python
class PartsUsage(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Tracks spare parts and consumables used in maintenance.
    Integrates with Inventory module.
    """

    work_order = ForeignKey(WorkOrder)

    # Inventory reference (assuming inventory.Item exists)
    item_id = BigIntegerField(null=True, blank=True)  # Reference to inventory.Item
    item_sku = CharField(max_length=100, blank=True)  # Denormalized for display
    item_name = CharField(max_length=200)

    # Usage
    quantity_used = DecimalField(max_digits=12, decimal_places=4)
    unit_of_measure = CharField(max_length=50, default='EA')

    # Source
    location_id = BigIntegerField(null=True, blank=True)  # inventory.Location
    location_code = CharField(max_length=100, blank=True)

    # Cost
    unit_cost = DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = TextField(blank=True)

    # Inventory transaction reference
    inventory_transaction_id = BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "maintenance_parts_usage"
```

---

## 4. Key Business Logic

### 4.1 Auto-Number Generation
- Asset Code: `AST-YYYY-NNNN`
- PM Task Number: `PMT-YYYY-NNNN`
- Request Number: `REQ-YYYY-NNNN`
- Work Order Number: `WO-YYYY-NNNN`

### 4.2 PM Schedule Generation
- When PMPlan is created/updated, auto-generate PMSchedules for applicable assets
- Calculate next_due_date based on frequency

### 4.3 PM Task Generation
- Daily job to check PMSchedules
- Create PMTask when schedule is due (within X days)

### 4.4 Work Order from Request
- Approved request auto-creates Work Order
- Links back to source request

### 4.5 Downtime Duration Calculation
```python
def save(self):
    if self.end_time and self.start_time:
        delta = self.end_time - self.start_time
        self.duration_minutes = int(delta.total_seconds() / 60)
    super().save()
```

### 4.6 QR Token Generation
```python
def generate_qr_token(self):
    if not self.qr_token:
        self.qr_token = f"AST-{self.public_id.hex[:12].upper()}"
    return self.qr_token
```

---

## 5. Permissions & Roles

### Role Matrix

| Role | Assets | PM Plans | Requests | Work Orders | Downtime | Reports |
|------|--------|----------|----------|-------------|----------|---------|
| Operator | View | View | Create | View Own | Record Start | - |
| Technician | View | View | View | Update Assigned | Record | - |
| Planner | Full | Full | Full | Full | Full | View |
| Manager | View | View | View | View | View | Full |
| Admin | Full | Full | Full | Full | Full | Full |

---

## 6. API Endpoints (URLs)

### Dashboard & Overview
- `GET /maintenance/` - Main dashboard
- `GET /maintenance/stats/` - JSON stats for charts

### Assets
- `GET /maintenance/assets/` - Asset list
- `GET /maintenance/assets/<pk>/` - Asset detail
- `POST /maintenance/assets/create/` - Create asset
- `PUT /maintenance/assets/<pk>/edit/` - Edit asset
- `GET /maintenance/assets/<pk>/qr/` - Generate QR code
- `GET /maintenance/assets/scan/<token>/` - Scan QR landing

### Preventive Maintenance
- `GET /maintenance/pm/plans/` - PM plans list
- `GET /maintenance/pm/calendar/` - PM calendar view
- `GET /maintenance/pm/tasks/` - PM tasks list
- `POST /maintenance/pm/tasks/<pk>/start/` - Start PM task
- `POST /maintenance/pm/tasks/<pk>/complete/` - Complete PM task

### Maintenance Requests
- `GET /maintenance/requests/` - Requests list
- `POST /maintenance/requests/create/` - Create request
- `POST /maintenance/requests/<pk>/approve/` - Approve request
- `POST /maintenance/requests/<pk>/reject/` - Reject request

### Work Orders
- `GET /maintenance/work-orders/` - Work orders list
- `GET /maintenance/work-orders/<pk>/` - Work order detail
- `POST /maintenance/work-orders/create/` - Create WO
- `POST /maintenance/work-orders/<pk>/start/` - Start WO
- `POST /maintenance/work-orders/<pk>/complete/` - Complete WO
- `POST /maintenance/work-orders/<pk>/parts/` - Add parts usage

### Downtime
- `GET /maintenance/downtime/` - Downtime events list
- `POST /maintenance/downtime/create/` - Record downtime
- `POST /maintenance/downtime/<pk>/end/` - End downtime
- `POST /maintenance/downtime/<pk>/impact/` - Add production impact
- `GET /maintenance/downtime/lost-sales/` - Lost sales view

### Settings
- `GET /maintenance/settings/` - Settings dashboard
- `GET /maintenance/settings/categories/` - Asset categories
- `GET /maintenance/settings/locations/` - Locations

---

## 7. Frontend Pages

### 7.1 Dashboard
- Summary cards: Open WOs, Overdue PMs, Total Downtime (month), Lost Revenue (month)
- Charts: Downtime by asset (top 5), WO status distribution, PM compliance rate
- Quick actions: Create request, View calendar, Open WOs

### 7.2 Asset Registry
- List with filters: category, location, status, criticality
- Asset detail with tabs: Info, Documents, Work Orders, Downtime History, Stats

### 7.3 PM Calendar
- Monthly/weekly view
- Color-coded: Green (completed), Yellow (due soon), Red (overdue), Blue (scheduled)
- Click to view/complete task

### 7.4 Work Order Board
- Grouped by status (Kanban-style or grouped tables)
- Filters: asset, priority, type, date range
- Detail page with all fields and parts usage

### 7.5 Downtime & Impact
- Timeline view of downtime events
- Impact summary with production links
- Lost sales table with totals

---

## 8. Integration Points

### 8.1 With Existing Modules

**HR Module:**
- Link assets to responsible employees
- Assign technicians from HREmployee
- Track who performed maintenance

**Inventory Module:**
- PartsUsage references inventory.Item
- Auto-deduct stock (future enhancement)
- Track maintenance costs

**Production Module:**
- ProductionImpact links to BatchOrder, JobCard
- Track delays and their causes

**QR Codes Module:**
- Generate QR codes for assets
- Scan to access asset actions quickly

**Knowledge Module:**
- Link PM plans to safety instructions/SOPs
- Reference technical documents

---

## 9. Assumptions & Future Enhancements

### Assumptions Made
1. Production module has BatchOrder and JobCard models (IDs stored as BigIntegerField for now)
2. Inventory module has Item model with SKU
3. HR module has HREmployee model
4. Users use Django's built-in auth system

### Future Enhancements
1. **Automatic Inventory Deduction**: When parts are logged, create inventory transaction
2. **Meter-Based PM**: Full implementation with meter reading tracking
3. **Mobile App**: Dedicated mobile views for technicians
4. **Email Notifications**: Alerts for overdue PMs, critical breakdowns
5. **Advanced Reporting**: PDF reports, trend analysis, predictive maintenance
6. **Vendor Management**: Track external service providers
7. **Equipment History**: Complete timeline of all events per asset

---

## 10. Implementation Priority

### Phase 1 (Core - Must Have)
1. Asset, AssetCategory, AssetLocation models
2. Basic asset CRUD views
3. MaintenanceRequest and WorkOrder models
4. Request → Work Order flow
5. Dashboard with basic stats

### Phase 2 (Preventive Maintenance)
1. PMPlan, PMSchedule, PMTask models
2. PM calendar view
3. PM task execution

### Phase 3 (Downtime & Impact)
1. DowntimeEvent model
2. ProductionImpact and LostSales
3. Downtime reporting

### Phase 4 (Integration & Polish)
1. Parts usage tracking
2. QR code integration
3. Advanced dashboards
4. Documentation and training

---

## 11. Database Table Summary

| Table Name | Purpose | Records (Est. Year 1) |
|------------|---------|------------------------|
| maintenance_asset_category | Asset types | 20-50 |
| maintenance_asset_location | Physical locations | 20-100 |
| maintenance_asset | Equipment registry | 100-500 |
| maintenance_asset_document | Asset documentation | 500-2000 |
| maintenance_pm_plan | PM templates | 50-200 |
| maintenance_pm_schedule | Asset-PM mappings | 500-2000 |
| maintenance_pm_task | PM task instances | 2000-10000/year |
| maintenance_request | Maintenance requests | 500-2000/year |
| maintenance_work_order | Work orders | 1000-5000/year |
| maintenance_wo_attachment | WO files | 2000-10000/year |
| maintenance_downtime_event | Downtime records | 1000-5000/year |
| maintenance_production_impact | Production delays | 500-2000/year |
| maintenance_lost_sales | Revenue impact | 100-500/year |
| maintenance_parts_usage | Parts consumed | 5000-20000/year |

---

This design provides a solid foundation for a comprehensive CMMS integrated with your existing Floor Management System. The schema is flexible enough to accommodate future enhancements while meeting immediate business needs for asset tracking, maintenance planning, and impact analysis.

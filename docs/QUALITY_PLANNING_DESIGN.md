# Quality Management & Planning/KPI Modules - Design Document

**Date:** November 17, 2025
**Version:** 1.0
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This document outlines the design for two integrated modules:
1. **Quality Management Module** - NCRs, calibration, acceptance criteria, quality disposition
2. **Planning & KPI Module** - Scheduling, capacity planning, performance metrics

**Key Design Principle:** Extend and integrate with existing Production and Evaluation modules rather than duplicate functionality.

---

## Module A: Quality Management

### A.1 Architecture Philosophy

**What Already Exists:**
- Cutter evaluation (Production: JobCutterEvaluationHeader/Detail, Evaluation: EvaluationCell)
- Thread inspection (ApiThreadInspection, ThreadInspection)
- NDT reports (NdtReport, NDTInspection)
- Checklists (JobChecklistInstance/Item)

**What Quality Module Adds:**
- Nonconformance management (NCR lifecycle)
- Equipment calibration control
- Acceptance criteria definitions
- Quality disposition workflow
- Defect analysis and root cause
- Quality metrics aggregation
- Customer-specific reporting requirements

### A.2 Quality Module Models

#### Reference Tables

```python
# DefectCategory - Classification of quality issues
class DefectCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    code = CharField(max_length=20, unique=True)  # e.g., "VISUAL", "DIMENSIONAL", "MATERIAL"
    name = CharField(max_length=100)
    description = TextField(blank=True)
    is_critical = BooleanField(default=False)  # Triggers immediate containment
    sort_order = PositiveIntegerField(default=0)

# RootCauseCategory - 5-Why / Ishikawa categories
class RootCauseCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    code = CharField(max_length=20, unique=True)  # "MAN", "MACHINE", "METHOD", "MATERIAL", "MEASUREMENT", "ENVIRONMENT"
    name = CharField(max_length=100)
    description = TextField(blank=True)
    sort_order = PositiveIntegerField(default=0)

# AcceptanceCriteriaTemplate - Reusable quality standards
class AcceptanceCriteriaTemplate(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    description = TextField()
    applies_to_bit_type = CharField(max_length=20, blank=True)  # e.g., "HDBS", "SMI"
    applies_to_customer = CharField(max_length=100, blank=True)  # e.g., "ARAMCO"
    applies_to_process = CharField(max_length=100, blank=True)  # e.g., "GRINDING", "BRAZING"

    # Criteria specifications (JSON for flexibility)
    criteria_json = JSONField(default=dict)  # {"max_wear_flat": 3.0, "min_exposure": 2.5, ...}

    # Standard references
    api_standard = CharField(max_length=100, blank=True)  # e.g., "API RP 7G-2"
    customer_spec = CharField(max_length=100, blank=True)
    internal_spec = CharField(max_length=100, blank=True)

    is_active = BooleanField(default=True)
    version = CharField(max_length=20, default="1.0")
```

#### Nonconformance Management

```python
# NonconformanceReport - Central NCR tracking
class NonconformanceReport(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    NCR_STATUS_CHOICES = [
        ('OPEN', 'Open - Under Investigation'),
        ('CONTAINED', 'Contained - Immediate Action Taken'),
        ('ROOT_CAUSE', 'Root Cause Analysis'),
        ('CORRECTIVE', 'Corrective Action In Progress'),
        ('VERIFICATION', 'Verification Pending'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    NCR_TYPE_CHOICES = [
        ('INTERNAL', 'Internal NC'),
        ('SUPPLIER', 'Supplier NC'),
        ('CUSTOMER', 'Customer Complaint'),
        ('PROCESS', 'Process Deviation'),
    ]

    ncr_number = CharField(max_length=50, unique=True)  # "NCR-2025-0001"
    ncr_type = CharField(max_length=20, choices=NCR_TYPE_CHOICES)
    status = CharField(max_length=20, choices=NCR_STATUS_CHOICES, default='OPEN')

    # What is nonconforming
    job_card_id = BigIntegerField(null=True, blank=True)  # production.JobCard
    serial_unit_id = BigIntegerField(null=True, blank=True)  # inventory.SerialUnit
    batch_order_id = BigIntegerField(null=True, blank=True)  # production.BatchOrder

    # Defect details
    defect_category = ForeignKey(DefectCategory)
    title = CharField(max_length=200)
    description = TextField()
    detection_point = CharField(max_length=100)  # Where discovered
    detection_method = CharField(max_length=100)  # How discovered

    # Quantity affected
    quantity_affected = PositiveIntegerField(default=1)
    quantity_contained = PositiveIntegerField(default=0)

    # Severity and impact
    severity = CharField(max_length=20)  # CRITICAL, MAJOR, MINOR
    customer_impact = BooleanField(default=False)
    production_impact = BooleanField(default=False)
    safety_impact = BooleanField(default=False)

    # Disposition
    DISPOSITION_CHOICES = [
        ('PENDING', 'Pending Decision'),
        ('USE_AS_IS', 'Use As Is'),
        ('REWORK', 'Rework'),
        ('REPAIR', 'Repair'),
        ('SCRAP', 'Scrap'),
        ('RETURN_SUPPLIER', 'Return to Supplier'),
        ('DOWNGRADE', 'Downgrade/Recategorize'),
    ]
    disposition = CharField(max_length=20, choices=DISPOSITION_CHOICES, default='PENDING')
    disposition_reason = TextField(blank=True)
    disposition_by = ForeignKey(User, null=True, blank=True)
    disposition_at = DateTimeField(null=True, blank=True)

    # Cost impact
    estimated_cost_impact = DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost_impact = DecimalField(max_digits=12, decimal_places=2, default=0)
    lost_revenue = DecimalField(max_digits=12, decimal_places=2, default=0)

    # Workflow
    reported_by = ForeignKey(User)
    reported_at = DateTimeField(auto_now_add=True)
    assigned_to = ForeignKey(User, null=True, blank=True)
    target_closure_date = DateField(null=True, blank=True)
    actual_closure_date = DateField(null=True, blank=True)
    closed_by = ForeignKey(User, null=True, blank=True)

# NCRRootCauseAnalysis - 5-Why analysis
class NCRRootCauseAnalysis(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    ncr = ForeignKey(NonconformanceReport)
    category = ForeignKey(RootCauseCategory)

    # 5-Why chain
    why_1 = TextField()
    why_2 = TextField(blank=True)
    why_3 = TextField(blank=True)
    why_4 = TextField(blank=True)
    why_5 = TextField(blank=True)

    root_cause_statement = TextField()
    is_systemic = BooleanField(default=False)  # Requires broader corrective action

    analyzed_by = ForeignKey(User)
    analyzed_at = DateTimeField(auto_now_add=True)

# NCRCorrectiveAction - CAPA tracking
class NCRCorrectiveAction(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    ACTION_TYPE_CHOICES = [
        ('IMMEDIATE', 'Immediate Containment'),
        ('CORRECTIVE', 'Corrective Action'),
        ('PREVENTIVE', 'Preventive Action'),
    ]

    ncr = ForeignKey(NonconformanceReport)
    action_type = CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    description = TextField()

    assigned_to = ForeignKey(User)
    due_date = DateField()
    completed_date = DateField(null=True, blank=True)

    status = CharField(max_length=20)  # PENDING, IN_PROGRESS, COMPLETED, VERIFIED
    effectiveness_verified = BooleanField(default=False)
    verification_notes = TextField(blank=True)
    verified_by = ForeignKey(User, null=True, blank=True)
    verified_at = DateTimeField(null=True, blank=True)
```

#### Equipment Calibration Control

```python
# CalibratedEquipment - Measuring instruments under control
class CalibratedEquipment(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    EQUIPMENT_TYPE_CHOICES = [
        ('TORQUE_WRENCH', 'Torque Wrench'),
        ('THREAD_GAUGE', 'Thread Gauge'),
        ('BORE_GAUGE', 'Bore Gauge'),
        ('MICROMETER', 'Micrometer'),
        ('CALIPER', 'Caliper'),
        ('LPT_KIT', 'LPT Testing Kit'),
        ('MPI_EQUIPMENT', 'MPI Equipment'),
        ('OTHER', 'Other'),
    ]

    equipment_id = CharField(max_length=50, unique=True)  # Internal ID tag
    name = CharField(max_length=200)
    equipment_type = CharField(max_length=50, choices=EQUIPMENT_TYPE_CHOICES)
    manufacturer = CharField(max_length=100, blank=True)
    model = CharField(max_length=100, blank=True)
    serial_number = CharField(max_length=100, blank=True)

    # Calibration requirements
    calibration_interval_days = PositiveIntegerField(default=365)
    calibration_procedure = TextField(blank=True)
    calibration_standard = CharField(max_length=100, blank=True)

    # Current status
    last_calibration_date = DateField(null=True, blank=True)
    next_calibration_due = DateField(null=True, blank=True)
    last_calibration_result = CharField(max_length=20, blank=True)  # PASS, FAIL, ADJUSTED

    STATUS_CHOICES = [
        ('IN_SERVICE', 'In Service - Calibration Current'),
        ('DUE_SOON', 'Due for Calibration Soon'),
        ('OVERDUE', 'Calibration Overdue - Do Not Use'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('UNDER_CALIBRATION', 'Under Calibration'),
    ]
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='IN_SERVICE')

    location = CharField(max_length=100, blank=True)
    custodian = CharField(max_length=100, blank=True)

    # Certificate tracking
    certificate_number = CharField(max_length=100, blank=True)
    calibration_lab = CharField(max_length=200, blank=True)

    is_critical = BooleanField(default=False)  # Critical for product quality

    def update_status(self):
        """Update status based on calibration due date."""
        from django.utils import timezone
        from datetime import timedelta

        if not self.next_calibration_due:
            return

        today = timezone.now().date()
        days_until_due = (self.next_calibration_due - today).days

        if days_until_due < 0:
            self.status = 'OVERDUE'
        elif days_until_due <= 30:
            self.status = 'DUE_SOON'
        else:
            self.status = 'IN_SERVICE'

# CalibrationRecord - History of calibrations
class CalibrationRecord(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    equipment = ForeignKey(CalibratedEquipment)

    calibration_date = DateField()
    performed_by = CharField(max_length=100)
    calibration_lab = CharField(max_length=200, blank=True)
    certificate_number = CharField(max_length=100)

    result = CharField(max_length=20)  # PASS, FAIL, ADJUSTED
    adjustments_made = TextField(blank=True)
    out_of_tolerance_findings = TextField(blank=True)

    # Measurements
    measurements_json = JSONField(default=dict)  # Actual measurement data

    next_due_date = DateField()
    cost = DecimalField(max_digits=10, decimal_places=2, default=0)

    # Document reference
    certificate_file = FileField(upload_to='quality/calibration/', blank=True, null=True)
```

#### Quality Disposition & Release

```python
# QualityDisposition - Final quality decision per job
class QualityDisposition(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    DECISION_CHOICES = [
        ('APPROVED', 'Approved - Meets All Requirements'),
        ('CONDITIONAL', 'Conditional Approval - With Deviations'),
        ('REJECTED', 'Rejected - Does Not Meet Requirements'),
        ('HOLD', 'On Quality Hold - Pending Review'),
    ]

    job_card_id = BigIntegerField()  # production.JobCard
    evaluation_session_id = BigIntegerField(null=True, blank=True)  # evaluation.EvaluationSession

    decision = CharField(max_length=20, choices=DECISION_CHOICES)
    disposition_date = DateTimeField(auto_now_add=True)

    # Who made the decision
    quality_engineer = ForeignKey(User)

    # Supporting evidence
    inspection_summary = TextField()
    deviations_accepted = TextField(blank=True)  # For conditional approval
    customer_concession = BooleanField(default=False)
    concession_reference = CharField(max_length=100, blank=True)

    # Acceptance criteria met
    acceptance_template = ForeignKey(AcceptanceCriteriaTemplate, null=True, blank=True)
    criteria_results_json = JSONField(default=dict)  # Actual vs required

    # NCRs linked
    ncrs_closed = ManyToManyField(NonconformanceReport, blank=True)

    # Certificate of Conformance
    coc_number = CharField(max_length=100, blank=True)
    coc_generated_at = DateTimeField(null=True, blank=True)

    notes = TextField(blank=True)
```

### A.3 Quality Module Integration Points

1. **With Production JobCard**: Link NCRs, dispositions, and quality holds
2. **With Evaluation Session**: Reference evaluations in quality decisions
3. **With Maintenance**: Equipment calibration schedules
4. **With HR**: Inspector qualifications and certifications
5. **With Inventory**: Defective material tracking

---

## Module B: Planning & KPI

### B.1 Architecture Philosophy

**What Already Exists:**
- BatchOrder (grouping jobs)
- JobCard (per-bit tracking)
- JobRoute/JobRouteStep (routing)
- OperationDefinition (process catalog)

**What Planning Module Adds:**
- Capacity planning and resource allocation
- Schedule generation and optimization
- WIP tracking and bottleneck analysis
- KPI calculation and trending
- Material requirement planning integration
- Delivery prediction and tracking

### B.2 Planning Module Models

#### Capacity & Resources

```python
# ResourceType - Categories of resources (machines, stations, skills)
class ResourceType(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=100)
    description = TextField(blank=True)
    category = CharField(max_length=50)  # MACHINE, STATION, SKILL, TOOL
    department = CharField(max_length=50, blank=True)

    # Capacity settings
    default_capacity_per_shift = DecimalField(max_digits=8, decimal_places=2, default=8)  # hours
    efficiency_factor = DecimalField(max_digits=5, decimal_places=2, default=0.85)  # 85% efficiency

    is_bottleneck = BooleanField(default=False)  # Known bottleneck resource
    is_active = BooleanField(default=True)

# ResourceCapacity - Available capacity by date
class ResourceCapacity(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    resource_type = ForeignKey(ResourceType)
    date = DateField()
    shift = CharField(max_length=20, blank=True)  # DAY, NIGHT, ALL

    # Available capacity
    available_hours = DecimalField(max_digits=8, decimal_places=2)
    reserved_hours = DecimalField(max_digits=8, decimal_places=2, default=0)  # For maintenance, etc.

    # Calculated load
    planned_load_hours = DecimalField(max_digits=8, decimal_places=2, default=0)
    actual_load_hours = DecimalField(max_digits=8, decimal_places=2, default=0)

    @property
    def utilization_percentage(self):
        if self.available_hours > 0:
            return (self.planned_load_hours / self.available_hours) * 100
        return 0

    @property
    def is_overloaded(self):
        return self.planned_load_hours > (self.available_hours - self.reserved_hours)

    class Meta:
        unique_together = ['resource_type', 'date', 'shift']
```

#### Schedule Management

```python
# ProductionSchedule - Master schedule container
class ProductionSchedule(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    name = CharField(max_length=200)
    schedule_date = DateField()  # Schedule effective date

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('FROZEN', 'Frozen - No Changes'),
        ('SUPERSEDED', 'Superseded by New Schedule'),
    ]
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    planning_horizon_days = PositiveIntegerField(default=30)

    # Scheduling parameters
    scheduling_algorithm = CharField(max_length=50, default='EARLIEST_DUE_DATE')
    priority_weighting = JSONField(default=dict)  # {"CRITICAL": 1.0, "RUSH": 0.8, ...}

    created_by = ForeignKey(User)
    published_at = DateTimeField(null=True, blank=True)
    published_by = ForeignKey(User, null=True, blank=True)

    notes = TextField(blank=True)

# ScheduledOperation - Planned operations in schedule
class ScheduledOperation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    schedule = ForeignKey(ProductionSchedule)

    # What is being scheduled
    job_card_id = BigIntegerField()  # production.JobCard
    job_route_step_id = BigIntegerField(null=True, blank=True)  # production.JobRouteStep
    operation_code = CharField(max_length=50)  # Reference to OperationDefinition

    # Schedule timing
    planned_start = DateTimeField()
    planned_end = DateTimeField()
    planned_duration_hours = DecimalField(max_digits=8, decimal_places=2)

    # Resource assignment
    resource_type = ForeignKey(ResourceType, null=True, blank=True)
    assigned_asset_id = BigIntegerField(null=True, blank=True)  # maintenance.Asset
    assigned_employee_id = BigIntegerField(null=True, blank=True)  # hr.HREmployee

    # Priority and sequence
    sequence_number = PositiveIntegerField(default=0)
    priority_score = DecimalField(max_digits=10, decimal_places=4, default=0)

    # Constraints
    earliest_start = DateTimeField(null=True, blank=True)  # After predecessor
    latest_end = DateTimeField(null=True, blank=True)  # Customer due date

    # Status
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('RELEASED', 'Released to Shop Floor'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING', 'Waiting'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')

    # Actual execution (updated from shop floor)
    actual_start = DateTimeField(null=True, blank=True)
    actual_end = DateTimeField(null=True, blank=True)
    actual_duration_hours = DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Delays and issues
    is_delayed = BooleanField(default=False)
    delay_reason = CharField(max_length=200, blank=True)
    delay_category = CharField(max_length=50, blank=True)  # MATERIAL, EQUIPMENT, QUALITY, LABOR

    # Material readiness
    materials_available = BooleanField(default=True)
    materials_shortage_list = TextField(blank=True)  # JSON list of missing items
```

#### KPI Tracking

```python
# KPIDefinition - Define what KPIs to track
class KPIDefinition(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    code = CharField(max_length=50, unique=True)
    name = CharField(max_length=200)
    description = TextField()

    CATEGORY_CHOICES = [
        ('DELIVERY', 'Delivery Performance'),
        ('QUALITY', 'Quality Metrics'),
        ('EFFICIENCY', 'Efficiency/Utilization'),
        ('COST', 'Cost Metrics'),
        ('SAFETY', 'Safety Metrics'),
    ]
    category = CharField(max_length=50, choices=CATEGORY_CHOICES)

    unit = CharField(max_length=50)  # %, hours, count, currency
    calculation_method = TextField()  # How to calculate

    # Targets
    target_value = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    warning_threshold = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    critical_threshold = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    # Higher is better or lower is better
    higher_is_better = BooleanField(default=True)

    aggregation_period = CharField(max_length=20)  # DAILY, WEEKLY, MONTHLY
    is_active = BooleanField(default=True)

# KPIValue - Actual KPI measurements
class KPIValue(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    kpi_definition = ForeignKey(KPIDefinition)

    # Time dimension
    period_start = DateField()
    period_end = DateField()

    # Value
    value = DecimalField(max_digits=12, decimal_places=4)

    # Context (optional - for drill-down)
    job_card_id = BigIntegerField(null=True, blank=True)
    batch_order_id = BigIntegerField(null=True, blank=True)
    customer_name = CharField(max_length=100, blank=True)
    employee_id = BigIntegerField(null=True, blank=True)
    asset_id = BigIntegerField(null=True, blank=True)

    # Calculated fields
    is_on_target = BooleanField(default=True)
    variance_from_target = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    notes = TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['kpi_definition', 'period_start']),
            models.Index(fields=['customer_name', 'period_start']),
        ]

# JobMetrics - Per-job performance metrics
class JobMetrics(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    job_card_id = BigIntegerField(unique=True)

    # Turnaround time
    total_turnaround_hours = DecimalField(max_digits=10, decimal_places=2, null=True)
    active_work_hours = DecimalField(max_digits=10, decimal_places=2, null=True)
    waiting_hours = DecimalField(max_digits=10, decimal_places=2, null=True)
    queue_hours = DecimalField(max_digits=10, decimal_places=2, null=True)

    # Quality metrics
    rework_count = PositiveIntegerField(default=0)
    ncr_count = PositiveIntegerField(default=0)
    defect_rate = DecimalField(max_digits=5, decimal_places=2, null=True)  # %

    # Delivery performance
    planned_completion = DateTimeField(null=True)
    actual_completion = DateTimeField(null=True)
    is_on_time = BooleanField(default=True)
    delay_days = IntegerField(default=0)

    # Cost performance
    estimated_cost = DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_variance = DecimalField(max_digits=12, decimal_places=2, default=0)

    # Last calculated
    calculated_at = DateTimeField(auto_now=True)
```

#### WIP Tracking

```python
# WIPSnapshot - Point-in-time WIP status
class WIPSnapshot(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    snapshot_time = DateTimeField()

    # Aggregates
    total_jobs_in_wip = PositiveIntegerField(default=0)
    jobs_on_track = PositiveIntegerField(default=0)
    jobs_at_risk = PositiveIntegerField(default=0)
    jobs_delayed = PositiveIntegerField(default=0)

    # By status
    jobs_in_evaluation = PositiveIntegerField(default=0)
    jobs_awaiting_approval = PositiveIntegerField(default=0)
    jobs_awaiting_materials = PositiveIntegerField(default=0)
    jobs_in_production = PositiveIntegerField(default=0)
    jobs_under_qc = PositiveIntegerField(default=0)
    jobs_on_hold = PositiveIntegerField(default=0)

    # Bottlenecks
    bottleneck_resources_json = JSONField(default=list)  # List of overloaded resources

    # Value in WIP
    total_wip_value = DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = TextField(blank=True)

# DeliveryForecast - Predicted delivery dates
class DeliveryForecast(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    job_card_id = BigIntegerField()
    batch_order_id = BigIntegerField(null=True, blank=True)

    # Customer commitment
    customer_required_date = DateField()

    # Forecast
    forecast_date = DateField()
    confidence_level = CharField(max_length=20)  # HIGH, MEDIUM, LOW

    # Risk factors
    risk_factors_json = JSONField(default=list)  # ["Material shortage", "Equipment down", ...]

    # Potential impact
    potential_delay_days = IntegerField(default=0)
    at_risk = BooleanField(default=False)

    # Actions needed
    actions_required = TextField(blank=True)

    calculated_at = DateTimeField(auto_now=True)
```

### B.3 Planning Module Integration Points

1. **With Production JobCard**: Schedule operations, track actual execution
2. **With Inventory**: Material availability for scheduling
3. **With Maintenance**: Equipment availability windows
4. **With Quality**: Rework impacts on schedule, quality metrics
5. **With HR**: Employee availability and qualifications

---

## Database Table Summary

### Quality Module (9 tables)
- `quality_defect_category`
- `quality_root_cause_category`
- `quality_acceptance_criteria_template`
- `quality_nonconformance_report`
- `quality_ncr_root_cause_analysis`
- `quality_ncr_corrective_action`
- `quality_calibrated_equipment`
- `quality_calibration_record`
- `quality_disposition`

### Planning Module (9 tables)
- `planning_resource_type`
- `planning_resource_capacity`
- `planning_production_schedule`
- `planning_scheduled_operation`
- `planning_kpi_definition`
- `planning_kpi_value`
- `planning_job_metrics`
- `planning_wip_snapshot`
- `planning_delivery_forecast`

---

## Key Design Decisions

1. **Loose coupling via IDs**: Use BigIntegerField for cross-module references to avoid circular imports
2. **JSON fields for flexibility**: Store complex/varying data structures (criteria, measurements) in JSONField
3. **Denormalization where appropriate**: Store calculated metrics to avoid expensive queries
4. **Status workflows**: Clear state machines for NCRs, schedules, dispositions
5. **Audit trail**: All models inherit PublicIdMixin, AuditMixin, SoftDeleteMixin
6. **Extensibility**: Generic structures that can accommodate future bit types (Roller Cone, Matrix)

---

## Implementation Priority

### Phase 1 (Core)
1. NCR lifecycle management
2. Equipment calibration tracking
3. Quality disposition workflow
4. Basic scheduling model
5. KPI definitions and values

### Phase 2 (Advanced)
1. Acceptance criteria templates
2. Resource capacity planning
3. WIP tracking and snapshots
4. Delivery forecasting
5. Advanced KPI dashboards

### Phase 3 (Integration)
1. Automatic schedule optimization
2. Material requirement integration
3. Real-time shop floor updates
4. Customer-specific reporting
5. Predictive analytics

---

This design provides a solid foundation for comprehensive quality management and production planning while leveraging existing functionality and maintaining clean architecture.

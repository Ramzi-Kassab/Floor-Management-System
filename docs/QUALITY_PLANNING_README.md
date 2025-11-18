# Quality Management & Planning/KPI Modules

## Overview

This document provides comprehensive documentation for two new integrated modules:

1. **Quality Management Module** - NCR lifecycle, calibration control, quality disposition
2. **Planning & KPI Module** - Scheduling, capacity planning, KPI tracking, WIP monitoring

Both modules are designed to integrate seamlessly with existing Production and Evaluation modules.

---

## Quality Management Module

### Purpose

The Quality Management module provides comprehensive quality control capabilities for PDC bit manufacturing operations, including:

- Nonconformance Report (NCR) lifecycle management
- Equipment calibration tracking and control
- Acceptance criteria templates
- Quality disposition and release authorization
- Root cause analysis (5-Why methodology)
- Corrective and preventive action (CAPA) tracking

### Key Models

#### Reference Tables
- **DefectCategory** - Classification of quality issues (VISUAL, DIMENSIONAL, MATERIAL, etc.)
- **RootCauseCategory** - Ishikawa categories (MAN, MACHINE, METHOD, MATERIAL, MEASUREMENT, ENVIRONMENT)
- **AcceptanceCriteriaTemplate** - Reusable quality standards with JSON-based criteria specifications

#### NCR Management
- **NonconformanceReport** - Central NCR tracking with complete lifecycle workflow
  - Status flow: OPEN → CONTAINED → ROOT_CAUSE → CORRECTIVE → VERIFICATION → CLOSED
  - Disposition options: USE_AS_IS, REWORK, REPAIR, SCRAP, RETURN_SUPPLIER, DOWNGRADE
  - Cost impact tracking (estimated vs actual)
  - Links to JobCard, SerialUnit, BatchOrder via loose coupling

- **NCRRootCauseAnalysis** - 5-Why analysis with systemic issue flagging
- **NCRCorrectiveAction** - CAPA tracking with effectiveness verification

#### Calibration Control
- **CalibratedEquipment** - Measuring instruments under calibration control
  - Equipment types: TORQUE_WRENCH, THREAD_GAUGE, BORE_GAUGE, MICROMETER, etc.
  - Status tracking: IN_SERVICE, DUE_SOON, OVERDUE, UNDER_CALIBRATION
  - Automatic status updates based on due dates

- **CalibrationRecord** - Historical calibration events with certificate tracking

#### Quality Disposition
- **QualityDisposition** - Final quality decision per job
  - Decisions: APPROVED, CONDITIONAL, REJECTED, HOLD
  - Certificate of Conformance (COC) generation
  - Customer concession tracking
  - Release authorization workflow

### URL Patterns

```
/quality/                           - Dashboard
/quality/ncrs/                      - NCR list
/quality/ncrs/create/               - Create NCR
/quality/ncrs/<pk>/                 - NCR detail
/quality/ncrs/<pk>/edit/            - Edit NCR
/quality/ncrs/<pk>/add-analysis/    - Add root cause analysis
/quality/ncrs/<pk>/add-action/      - Add corrective action
/quality/ncrs/<pk>/close/           - Close NCR

/quality/calibration/               - Calibration overview
/quality/calibration/equipment/     - Equipment list
/quality/calibration/due/           - Equipment due for calibration
/quality/calibration/overdue/       - Overdue calibrations

/quality/dispositions/              - Disposition list
/quality/dispositions/create/       - Create disposition
/quality/dispositions/<pk>/release/ - Authorize release
/quality/dispositions/<pk>/generate-coc/ - Generate COC

/quality/criteria/                  - Acceptance criteria templates
/quality/reports/                   - Reports dashboard
/quality/settings/                  - Settings
```

### Admin Interface

Full admin interface with:
- Fieldsets organized by functional area
- Inline editing for related objects (analyses, actions, calibration records)
- Custom list displays with status indicators
- Bulk actions (update calibration status, generate COC numbers, authorize releases)
- Rich filtering and search capabilities

---

## Planning & KPI Module

### Purpose

The Planning & KPI module provides production planning and performance monitoring capabilities:

- Resource capacity planning and utilization tracking
- Production schedule management
- KPI definition and measurement
- Work-in-Progress (WIP) monitoring
- Delivery forecasting and risk management
- Job-level metrics tracking

### Key Models

#### Resource Management
- **ResourceType** - Categories of resources (MACHINE, STATION, SKILL, TOOL, AREA)
  - Default capacity settings
  - Efficiency factors
  - Bottleneck identification

- **ResourceCapacity** - Daily capacity planning
  - Available vs reserved hours
  - Planned vs actual load
  - Utilization percentage calculation

#### Schedule Management
- **ProductionSchedule** - Master schedule container
  - Status workflow: DRAFT → PUBLISHED → FROZEN
  - Scheduling algorithms: EARLIEST_DUE_DATE, CRITICAL_RATIO, PRIORITY_WEIGHTED
  - Planning horizon configuration

- **ScheduledOperation** - Individual scheduled operations
  - Links to JobCard and JobRouteStep
  - Resource assignment
  - Priority scoring
  - Delay tracking with categories (MATERIAL, EQUIPMENT, QUALITY, LABOR)
  - Material availability tracking

#### KPI Tracking
- **KPIDefinition** - KPI configuration
  - Categories: DELIVERY, QUALITY, EFFICIENCY, COST, SAFETY, PRODUCTIVITY
  - Target values with warning and critical thresholds
  - Higher/lower is better configuration
  - Aggregation periods (DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY)

- **KPIValue** - Actual measurements
  - Context support for drill-down (by job, customer, employee, asset, department)
  - Automatic variance calculation
  - Status evaluation (ON_TARGET, WARNING, CRITICAL)

#### Metrics & Forecasting
- **JobMetrics** - Per-job performance metrics
  - Turnaround time breakdown (active work, waiting, queue)
  - Quality metrics (rework count, NCR count, defect rate)
  - Delivery performance (on-time, delay days)
  - Cost performance (estimated vs actual)
  - Flow efficiency calculation

- **WIPSnapshot** - Point-in-time WIP status
  - Job counts by status/stage
  - Health score calculation
  - Bottleneck identification
  - Value and age metrics

- **DeliveryForecast** - Delivery risk management
  - Customer required date vs forecast date
  - Confidence levels (HIGH, MEDIUM, LOW)
  - Risk factor tracking
  - Escalation requirements
  - Urgency level calculation

### URL Patterns

```
/planning/                              - Dashboard
/planning/resources/                    - Resource types
/planning/capacity/                     - Capacity overview
/planning/capacity/bottlenecks/         - Bottleneck analysis

/planning/schedules/                    - Schedule list
/planning/schedules/create/             - Create schedule
/planning/schedules/<pk>/               - Schedule detail
/planning/schedules/<pk>/publish/       - Publish schedule

/planning/operations/<pk>/              - Operation detail
/planning/operations/<pk>/start/        - Start operation
/planning/operations/<pk>/complete/     - Complete operation

/planning/kpis/                         - KPI dashboard
/planning/kpis/definitions/             - KPI definitions
/planning/kpis/values/                  - KPI values
/planning/kpis/values/record/           - Record KPI value
/planning/kpis/trends/                  - KPI trends

/planning/wip/                          - WIP board
/planning/wip/snapshot/                 - Create WIP snapshot
/planning/wip/history/                  - WIP history

/planning/metrics/                      - Metrics overview
/planning/forecasts/                    - Delivery forecasts
/planning/forecasts/at-risk/            - At-risk jobs

/planning/reports/                      - Reports dashboard
/planning/reports/otd/                  - On-Time Delivery report
/planning/reports/utilization/          - Utilization report
/planning/settings/                     - Settings
```

### Admin Interface

Comprehensive admin with:
- Resource capacity management
- Schedule publishing and freezing
- KPI value tracking with target evaluation
- WIP snapshot history
- Delivery forecast risk analysis
- Bulk operations for schedule management

---

## Integration Points

### With Production Module
- NCRs link to JobCard via `job_card_id`
- Quality dispositions reference evaluation sessions
- Scheduled operations link to JobRouteSteps
- Job metrics reference production jobs

### With Evaluation Module
- Quality dispositions reference EvaluationSession
- Cutter evaluation results feed into quality assessments
- Inspection results inform NCR creation

### With Inventory Module
- NCRs can reference SerialUnits
- Material availability affects scheduling
- Quality holds impact inventory status

### With HR Module
- NCR assignments and quality engineer roles
- Employee KPIs reference HR employees
- Resource capacity considers labor availability

### With Maintenance Module
- Calibrated equipment links to maintenance assets
- Equipment availability affects scheduling
- Downtime impacts capacity planning

---

## Database Tables

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

## Getting Started

### 1. Run Migrations

```bash
python manage.py makemigrations quality planning
python manage.py migrate
```

### 2. Create Initial Data

Via Django Admin or shell:

```python
# Quality - Defect Categories
from floor_app.operations.quality.models import DefectCategory
DefectCategory.objects.create(code='VISUAL', name='Visual Defect', sort_order=1)
DefectCategory.objects.create(code='DIMENSIONAL', name='Dimensional Issue', sort_order=2)
DefectCategory.objects.create(code='MATERIAL', name='Material Defect', is_critical=True, sort_order=3)

# Quality - Root Cause Categories (Ishikawa)
from floor_app.operations.quality.models import RootCauseCategory
RootCauseCategory.objects.create(code='MAN', name='Man/People', sort_order=1)
RootCauseCategory.objects.create(code='MACHINE', name='Machine/Equipment', sort_order=2)
RootCauseCategory.objects.create(code='METHOD', name='Method/Process', sort_order=3)
RootCauseCategory.objects.create(code='MATERIAL', name='Material', sort_order=4)
RootCauseCategory.objects.create(code='MEASUREMENT', name='Measurement', sort_order=5)
RootCauseCategory.objects.create(code='ENVIRONMENT', name='Environment', sort_order=6)

# Planning - KPI Definitions
from floor_app.operations.planning.models import KPIDefinition
KPIDefinition.objects.create(
    code='OTD',
    name='On-Time Delivery',
    description='Percentage of jobs delivered on or before customer required date',
    category='DELIVERY',
    unit='%',
    calculation_method='(Jobs On Time / Total Jobs) * 100',
    target_value=95.00,
    warning_threshold=90.00,
    critical_threshold=85.00,
    higher_is_better=True,
    show_on_dashboard=True
)
```

### 3. Access the Modules

- Quality Dashboard: `/quality/`
- Planning Dashboard: `/planning/`
- Django Admin: `/admin/` (full CRUD operations)

---

## Future Enhancements

### Phase 2 (Planned)
1. Customer-specific report generation (ARAMCO compact view)
2. Automatic NCR number sequencing by type
3. Advanced scheduling algorithms
4. Real-time shop floor integration
5. Predictive delivery forecasting

### Phase 3 (Future)
1. Statistical Process Control (SPC) charts
2. Machine learning for root cause prediction
3. Automated capacity optimization
4. Customer portal for quality certificates
5. Mobile app for shop floor operations

---

## Technical Notes

### Design Patterns
- **Loose Coupling**: Cross-module references use BigIntegerField instead of ForeignKey to avoid circular imports
- **JSON Fields**: Flexible data storage for criteria, measurements, risk factors
- **Status Workflows**: Clear state machines with choices tuples
- **Mixins**: PublicIdMixin, AuditMixin, SoftDeleteMixin for consistency
- **Explicit Naming**: db_table and index names follow module conventions

### Performance Considerations
- Database indexes on frequently queried fields
- Select_related in admin queries
- Paginated list views
- Denormalized metrics for dashboard performance

### Security
- Login required for all views
- User tracking for audit trail
- Protected ForeignKey relationships
- Form validation for all inputs

---

## Support

For questions or issues:
- Check existing documentation in `/docs/`
- Review admin interface for data management
- Consult Django logs for error details
- Reference existing module patterns for consistency

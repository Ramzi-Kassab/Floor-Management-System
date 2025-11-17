# Central QR/Barcode Service for Floor Management System

A comprehensive QR code and barcode scanning infrastructure that provides unified tracking across all modules of the PDC Bit Manufacturing Floor Management System.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Models](#core-models)
4. [Scan Workflows](#scan-workflows)
5. [BOM Material Pickup](#bom-material-pickup)
6. [Process Execution](#process-execution)
7. [Equipment & Maintenance](#equipment--maintenance)
8. [API Reference](#api-reference)
9. [Installation](#installation)
10. [Extending the System](#extending-the-system)
11. [Security](#security)

---

## Overview

The QR Code Service provides a **central identity and routing layer** for the entire Floor Management System. It enables:

- **Universal QR Code Generation**: Create QR codes for any entity (Employee, Job Card, Equipment, Serial Unit, etc.)
- **Comprehensive Audit Trail**: Track WHO scanned WHAT, WHEN, WHERE, and WHY
- **Smart Routing**: Automatically route scans to appropriate domain handlers
- **Process Tracking**: Start/End/Pause/Resume production steps via scanning
- **Equipment Maintenance**: Quick issue reporting through QR scanning
- **Inventory Movement**: Track materials from BOM pickup to final location
- **Compliance**: Full audit trail for ISO/API certification requirements

---

## Architecture

### Central Design Principle

```
QR Code Scan → Central Handler → Domain Logic → Result + Audit Log
```

The QR service uses **Generic Foreign Keys** to link QR codes to any Django model without tight coupling:

```python
class QCode(Model):
    token = UUIDField(unique=True)  # The QR payload
    qcode_type = CharField()         # EMPLOYEE, JOB_CARD, etc.
    content_type = ForeignKey(ContentType)  # Generic FK
    object_id = BigIntegerField()
    target_object = GenericForeignKey()
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **QCode** | Central identity model linking tokens to target objects |
| **ScanLog** | Comprehensive audit trail for all scans |
| **ScanHandler** | Routes scans to domain-specific handlers |
| **QRCodeGenerator** | Creates QR/barcode images (PNG/SVG) |
| **ProcessExecution** | State machine for production step tracking |
| **MovementLog** | WHO/WHAT/WHEN/WHERE/WHY for inventory movements |
| **Equipment** | Master data for machines and tools |
| **MaintenanceRequest** | Maintenance workflow management |
| **Container** | Bit boxes, bins, pallets for logistics |

---

## Core Models

### QCode (Central Identity)

```python
from floor_app.operations.qrcodes.models import QCode, QCodeType

# Create a QCode for an employee
qcode = QCode.objects.create_for_object(
    obj=employee,
    qcode_type=QCodeType.EMPLOYEE,
    label=f"Badge: {employee.employee_no}",
    created_by=user
)

# Get scan URL (what's embedded in QR)
url = qcode.get_scan_url()  # /qrcodes/scan/<uuid>/

# Get QR image URL
img_url = qcode.get_image_url()  # /qrcodes/img/<uuid>.png
```

**Supported QCode Types:**
- `EMPLOYEE` - Employee badges
- `JOB_CARD` - Production work orders
- `PROCESS_STEP` - Route step execution
- `BIT_SERIAL` - Individual PDC bits (SerialUnit)
- `BIT_BOX` - Containers for bits
- `EQUIPMENT` - Machines and tools
- `LOCATION` - Warehouse locations
- `ITEM` - Inventory items
- `BOM_MATERIAL` - BOM line item pickup
- `EVALUATION_SESSION` - Evaluation records
- `BATCH_ORDER` - Production batches

### ScanLog (Audit Trail)

Every scan is logged with:

```python
ScanLog.create_log(
    qcode=qcode,
    action_type=ScanActionType.PROCESS_START,
    request=request,  # Auto-extracts user, IP, user agent
    success=True,
    message="Started process step: De-braze cutters",
    reason="Production order #12345",
    context_obj=job_card,  # Optional related object
    metadata={'work_center': 'BAY-1'}
)
```

**Action Types:**
- `VIEW_DETAILS` - View object information
- `PROCESS_START` - Start production step
- `PROCESS_END` - Complete production step
- `PROCESS_PAUSE` / `PROCESS_RESUME` - Pause/resume tracking
- `MOVE_ITEM` - Move to location
- `MAINTENANCE_REPORT` - Report equipment issue
- `MATERIAL_PICKUP` / `MATERIAL_RETURN` - BOM operations
- `CHECK_IN` / `CHECK_OUT` - Attendance
- `LOCATION_ASSIGN` - Assign to location
- `QUALITY_CHECK` - Inspection scans

---

## Scan Workflows

### Employee Badge Scan

When an employee badge QR is scanned:

1. Central handler receives scan
2. Validates QCode is active
3. Presents options:
   - View Profile
   - Check In
   - Check Out
4. Logs scan with WHO/WHEN/WHERE

```python
# Scan URL
GET /qrcodes/scan/{employee_qcode_token}/

# Result
{
  "success": true,
  "action": "VIEW_DETAILS",
  "message": "Employee badge scanned",
  "show_options": true,
  "options": [
    {"action": "view_profile", "label": "View Profile"},
    {"action": "check_in", "label": "Check In"},
    {"action": "check_out", "label": "Check Out"}
  ]
}
```

### Job Card Scan

```python
# Scanning a job card QR opens the job card detail page
GET /qrcodes/scan/{job_card_qcode_token}/
# Redirects to /production/jobcards/{pk}/
```

### Equipment Scan

```python
# Options presented:
# - View Details
# - Report Issue (creates MaintenanceRequest)
# - Maintenance History

# Quick maintenance reporting:
POST /qrcodes/equipment/{pk}/report/
{
  "title": "Grinding wheel worn",
  "description": "Wheel showing uneven wear pattern",
  "priority": "HIGH",
  "maintenance_type": "CORRECTIVE"
}
```

---

## BOM Material Pickup

When materials are needed for a job card, the BOM Material QR workflow tracks:

### 1. Generate QR for BOM Line

```python
from floor_app.operations.qrcodes.models import QCode, QCodeType

# Each BOM line can have a QR code
qcode = QCode.objects.create_for_object(
    obj=bom_line,
    qcode_type=QCodeType.BOM_MATERIAL,
    label=f"BOM: {bom_line.item.sku} x {bom_line.quantity}",
    created_by=user
)
```

### 2. Scan for Pickup

Worker scans the BOM material QR:

```python
GET /qrcodes/scan/{bom_qcode_token}/
# Shows options: Pickup, Return, Verify
```

### 3. Record Pickup

```python
# API or form submission
POST /qrcodes/bom/pickup/{bom_line_id}/
{
  "quantity": 25,
  "notes": "Partial pickup for Job Card JC-2024-001"
}

# Creates MovementLog entry:
{
  "movement_type": "BOM_PICKUP",
  "bom_line_id": 123,
  "quantity": 25,
  "moved_by_user": user,
  "moved_by_employee_id": 45,
  "moved_by_name": "John Smith",
  "job_card_id": 789,
  "reason": "BOM material pickup",
  "moved_at": "2024-11-17T10:30:00Z"
}
```

### 4. Track Returns

Unused materials are returned:

```python
POST /qrcodes/bom/return/{bom_line_id}/
{
  "quantity": 5,
  "notes": "Excess material - returning to stock"
}

# Creates MovementLog with type "BOM_RETURN"
```

### Key Features:

- **Complete Traceability**: Every pickup/return logged with timestamp
- **Employee Attribution**: Links to HR Employee for accountability
- **Job Card Context**: Materials tied to specific production orders
- **Cost Tracking**: Unit cost captured at movement time
- **Verification Support**: Optional verification workflow

---

## Process Execution

The Process Execution system enables **time tracking via QR scanning** for production steps.

### State Machine

```
NOT_STARTED → IN_PROGRESS → COMPLETED
                   ↓
                PAUSED ← → IN_PROGRESS
```

### Workflow

1. **First Scan**: Start process step
2. **Second Scan**: Show options (End, Pause)
3. **Pause Scan**: Pause with reason
4. **Resume Scan**: Continue from pause
5. **Final Scan**: Complete step

### Example: De-braze Cutters Operation

```python
# Worker scans PROCESS_STEP QR code
GET /qrcodes/scan/{process_step_qcode_token}/

# First scan - Start
ProcessExecution.objects.create(
    job_card_id=789,
    route_step_id=123,
    operation_name="De-braze cutters",
    operator_employee_id=45,
    operator_name="John Smith",
    status="IN_PROGRESS",
    start_time=now()
)

# Later - Pause for lunch
execution.pause(reason="Lunch break")
# Creates ProcessPause record with pause_start

# After lunch - Resume
execution.resume()
# Sets pause_end, updates total_pause_minutes

# Complete the step
execution.end(completion_notes="All cutters removed successfully")
# Sets end_time, status="COMPLETED"
# Duration calculated: (end_time - start_time) - total_pause_minutes
```

### Time Tracking Benefits

- **Accurate Labor Hours**: Excludes pause time
- **KPI Calculation**: Track efficiency by operation
- **Operator Attribution**: WHO did WHAT
- **Work Center Tracking**: WHERE it was done
- **Quality Metrics**: Defects found during step

---

## Equipment & Maintenance

### Equipment Model

```python
from floor_app.operations.qrcodes.models import Equipment

equipment = Equipment.objects.create(
    code="CNC-001",
    name="CNC Lathe Machine",
    equipment_type="MACHINE",
    manufacturer="Haas Automation",
    model_number="ST-20Y",
    serial_number="SN-2023-001",
    status="OPERATIONAL",
    maintenance_interval_days=90,
    next_maintenance_date=date(2025, 1, 1)
)

# Generate QR code for equipment
qcode, created = QCode.get_or_create_for_object(
    obj=equipment,
    qcode_type=QCodeType.EQUIPMENT,
    label=f"{equipment.code} - {equipment.name}"
)
equipment.qcode_id = qcode.pk
equipment.save()
```

### Quick Maintenance Reporting

Worker scans equipment QR when issue discovered:

```python
# 1. Scan equipment QR
# 2. Select "Report Issue"
# 3. Fill form:
POST /qrcodes/equipment/{pk}/report/
{
  "title": "Abnormal vibration",
  "description": "High vibration during high-speed operations",
  "priority": "HIGH",
  "maintenance_type": "CORRECTIVE"
}

# Creates MaintenanceRequest with:
# - Reporter info (from session)
# - Equipment reference
# - Timestamp
# - Scan log entry
```

### Maintenance Workflow

1. **OPEN** - Issue reported
2. **ACKNOWLEDGED** - Technician assigned
3. **IN_PROGRESS** - Work started
4. **WAITING_PARTS** - Parts on order
5. **COMPLETED** - Issue resolved

### Completion

```python
# Complete maintenance
request.complete(
    resolution_notes="Replaced worn bearing",
    parts_used="SKF 6205-2RS bearing",
    labor_hours=2.5,
    total_cost=450.00
)

# Automatically updates:
# - Equipment.last_maintenance_date
# - Equipment.next_maintenance_date (if interval set)
# - Equipment.status = OPERATIONAL
```

---

## API Reference

### REST Endpoints

```python
# Scan a QR code (AJAX/Web)
GET /qrcodes/scan/{token}/

# API scan (JSON)
POST /qrcodes/api/scan/
{
  "token": "uuid-string",
  "action_hint": "view_details"
}

# Get QCode info
GET /qrcodes/api/qcode/{token}/

# QR image generation
GET /qrcodes/img/{token}.png
GET /qrcodes/img/{token}.svg
GET /qrcodes/img/label/{token}/  # With label text
```

### Response Format

```json
{
  "success": true,
  "action": "PROCESS_START",
  "message": "Started De-braze cutters",
  "redirect_url": "/qrcodes/process/action/123/",
  "show_options": false,
  "options": [],
  "data": {
    "execution_id": 123,
    "duration_minutes": 45.5
  }
}
```

---

## Installation

### 1. Prerequisites

```bash
# Install QR code generation libraries
pip install qrcode[pil]
pip install python-barcode[images]
```

### 2. Add to INSTALLED_APPS

```python
# floor_mgmt/settings.py
INSTALLED_APPS = [
    # ... existing apps
    'floor_app.operations.qrcodes.apps.QRCodesConfig',
]
```

### 3. Add URL Configuration

```python
# floor_mgmt/urls.py
urlpatterns = [
    # ... existing URLs
    path("qrcodes/", include(("floor_app.operations.qrcodes.urls", "qrcodes"), namespace="qrcodes")),
]
```

### 4. Run Migrations

```bash
python manage.py makemigrations qrcodes
python manage.py migrate qrcodes
```

### 5. Load Seed Data

```bash
python manage.py loaddata floor_app/operations/qrcodes/fixtures/initial_data.json
```

### 6. Access Dashboard

Navigate to `/qrcodes/` to see the QR Code Management dashboard.

---

## Extending the System

### Adding a New QCode Type

1. **Add type constant:**

```python
# models/qcode.py
class QCodeType:
    # ... existing types
    TOOL = 'TOOL'

    CHOICES = (
        # ... existing choices
        (TOOL, 'Tool'),
    )
```

2. **Add handler method:**

```python
# services/handlers.py
class ScanHandler:
    def _get_handler_for_type(self, qcode_type):
        handlers = {
            # ... existing handlers
            QCodeType.TOOL: self._handle_tool,
        }
        return handlers.get(qcode_type)

    def _handle_tool(self, qcode, action_hint=None, context_obj=None, reason=""):
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Tool scanned",
            redirect_url=f'/tools/{qcode.object_id}/',
            data={'tool_id': qcode.object_id}
        )
```

3. **Update content type mapping:**

```python
# views.py - generate_qcode function
content_type_map = {
    # ... existing mappings
    'TOOL': ('tools', 'tool'),
}
```

### Custom Scan Actions

```python
# Add new action type
class ScanActionType:
    # ... existing actions
    TOOL_CHECKOUT = 'TOOL_CHECKOUT'

    CHOICES = (
        # ... existing choices
        (TOOL_CHECKOUT, 'Tool Checkout'),
    )
```

### Integration with Existing Modules

The QR service integrates with your existing modules:

- **HR**: Employee badges, operator attribution
- **Production**: Job cards, route steps, process timing
- **Inventory**: Serial units, BOMs, stock movements
- **Evaluation**: Session tracking

Example integration:

```python
# In your JobCard model or view
from floor_app.operations.qrcodes.models import QCode, QCodeType

def generate_job_card_qr(job_card, user):
    """Auto-generate QR code when job card is created."""
    qcode, created = QCode.get_or_create_for_object(
        obj=job_card,
        qcode_type=QCodeType.JOB_CARD,
        label=f"Job Card: {job_card.job_card_number}",
        created_by=user
    )
    return qcode
```

---

## Security

### Token Security

- **UUID4 tokens**: Non-guessable, randomly generated
- **No sensitive data in QR**: Token is opaque; all data resolved server-side
- **Revocation support**: Deactivate compromised tokens
- **Version tracking**: Regenerate tokens when needed

### Access Control

- **Authentication required**: All views require login
- **Domain-level authorization**: Delegates to domain views
- **Rate limiting**: Prevent token enumeration (implement at web server level)
- **IP logging**: Track scan locations for audit

### Audit Compliance

- **Complete audit trail**: Every scan logged with WHO/WHAT/WHEN/WHERE/WHY
- **Immutable logs**: ScanLog entries cannot be deleted
- **Exportable**: CSV export for compliance reporting
- **Tamper-evident**: Timestamps and user attribution

### Best Practices

1. **Print labels with version**: Include version number on printed labels
2. **Regular audits**: Review deactivated codes and failed scans
3. **Employee training**: Ensure proper scan procedures
4. **Backup strategy**: Regular database backups include scan history
5. **HTTPS**: Always serve over HTTPS in production

---

## Dashboard & Management

The QR Code Dashboard (`/qrcodes/`) provides:

- **Statistics**: Total codes, scans today, active processes
- **Equipment alerts**: Maintenance overdue indicators
- **Recent activity**: Latest scans and movements
- **Quick actions**: Generate codes, print labels, manage equipment

### Admin Interface

Full Django Admin integration for:
- QCode management (list, search, filter by type)
- Scan log analysis (by date, user, action type)
- Equipment CRUD operations
- Maintenance request tracking
- Container management

---

## File Structure

```
floor_app/operations/qrcodes/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── qcode.py              # Central QCode model
│   ├── scan_log.py           # Audit trail
│   ├── process_execution.py  # State machine for processes
│   ├── maintenance.py        # Equipment & requests
│   └── movement.py           # Inventory tracking
├── services/
│   ├── __init__.py
│   ├── generator.py          # QR/Barcode image generation
│   └── handlers.py           # Central scan routing
├── admin/
│   └── __init__.py           # Django Admin registrations
├── forms/
│   └── __init__.py           # Form definitions
├── views.py                  # Views (933 lines)
├── urls.py                   # URL patterns (60+ routes)
├── templates/qrcodes/
│   ├── dashboard.html
│   ├── qcode_list.html
│   ├── qcode_detail.html
│   ├── equipment_*.html
│   ├── maintenance_*.html
│   ├── container_*.html
│   ├── process_*.html
│   ├── bom_*.html
│   └── ... (25+ templates)
├── fixtures/
│   └── initial_data.json     # Seed data
├── migrations/
│   └── __init__.py
└── tests/
    └── __init__.py
```

---

## Summary

The Central QR/Barcode Service provides:

1. **Unified Identity**: One system for all QR codes across all modules
2. **Complete Traceability**: WHO did WHAT, WHEN, WHERE, WHY
3. **Smart Routing**: Automatic handling based on QCode type
4. **Process Tracking**: Start/End/Pause/Resume with accurate time calculation
5. **Equipment Management**: Quick maintenance reporting via scanning
6. **BOM Material Tracking**: Pickup/return workflow for job cards
7. **Compliance Ready**: Full audit trail for ISO/API requirements
8. **Extensible Architecture**: Easy to add new types and handlers
9. **Modern UI**: Bootstrap 5 dashboard with statistics and quick actions
10. **API Support**: JSON endpoints for mobile/scanner integration

**Total Implementation:**
- 7 core models with comprehensive fields
- 60+ URL routes
- 25+ templates
- 933+ lines of view logic
- Full admin integration
- Seed data fixtures
- Image generation service
- Central scan handler with routing

This service transforms your floor operations from paper-based tracking to a fully digital, QR-enabled workflow system.

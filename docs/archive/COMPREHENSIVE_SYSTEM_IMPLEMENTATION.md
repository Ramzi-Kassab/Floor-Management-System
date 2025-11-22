# Comprehensive System Implementation Plan

## 🎯 Overview

Building an integrated system with:
1. **Multi-Channel Notifications** (WhatsApp, Email, SMS, Push, In-app)
2. **Approval Workflows** (Visible to all concerned parties)
3. **Enhanced QR Code System** (Production, Inventory, Logistics)
4. **GPS Address Verification**
5. **Phone ID Employee Tracking**
6. **+ All Previous Enhancements** (APIs, Excel, Scanning, etc.)

---

## ✅ Completed (Just Now)

### 1. Notification & Announcement System (Models)
**File**: `/floor_app/operations/notifications/models/__init__.py`

**Core Models Created:**
- `NotificationChannel` - Configure channels (WhatsApp, Email, SMS, Push, In-app, Telegram)
- `NotificationTemplate` - Reusable message templates with variables
- `NotificationPreference` - User preferences per channel
- `Notification` - Individual notification records
- `NotificationDelivery` - Per-channel delivery tracking
- `Announcement` - System-wide announcements
- `AnnouncementRead` - Read tracking

**Features**:
✅ Multi-channel support (6 channels)
✅ Priority levels (Low, Normal, High, Urgent)
✅ Template system with variables
✅ User preferences (enable/disable per channel)
✅ Quiet hours support
✅ Read/unread tracking
✅ Delivery status tracking
✅ Rate limiting per channel
✅ Expiry dates for time-sensitive notifications
✅ Action buttons with URLs
✅ Rich content (images, attachments)
✅ Targeted delivery (All, Department, Role, Location, Custom)

### 2. Approval Workflow System (Models)
**File**: `/floor_app/operations/approvals/models/__init__.py`

**Core Models Created:**
- `ApprovalWorkflow` - Define workflow templates
- `ApprovalLevel` - Multi-level approval chains
- `ApprovalRequest` - Individual approval instances
- `ApprovalStep` - Per-approver steps
- `ApprovalHistory` - Complete audit trail
- `ApprovalDelegation` - Persistent delegation rules

**Features:**
✅ Multi-level approval chains (sequential/parallel)
✅ Role-based approvers
✅ Approval modes (Sequential, Parallel, Any One, Majority, All)
✅ Auto-approval rules
✅ Conditional approvals
✅ Delegation support
✅ Escalation (SLA tracking)
✅ Complete audit trail
✅ **Visibility control** (visible_to_all, visible_to_departments, visible_to_users)
✅ Integration with notifications
✅ Generic foreign key (approve anything)
✅ Status tracking (Draft, Submitted, In Progress, Approved, Rejected, Cancelled, Escalated)

---

## 🚧 In Progress (Services Layer)

### 3. Notification Delivery Services

**What's Needed:**
```python
# Main orchestration service
NotificationService:
  - send(notification, channels)
  - send_bulk(notifications)
  - send_announcement(announcement)
  - send_approval_request(request, approver)
  - send_approval_approved(request)
  - send_approval_rejected(request, reason)
  - render_template(template, variables)
  - check_user_preferences(user)
  - respect_quiet_hours(user)

# Channel-specific services
WhatsAppService:
  - send_message(phone, message)
  - send_template(phone, template_name, params)
  - check_delivery_status(message_id)
  - Uses: Twilio WhatsApp API or WhatsApp Business API

EmailService:
  - send_email(to, subject, body, html=True)
  - send_bulk_email(recipients, subject, body)
  - Uses: Django SMTP or Microsoft Graph API (for Outlook)

SMSService:
  - send_sms(phone, message)
  - Uses: Twilio SMS API

PushNotificationService:
  - send_push(device_token, title, body, data)
  - send_to_topic(topic, title, body)
  - Uses: Firebase Cloud Messaging (FCM)

TelegramService:
  - send_message(chat_id, message)
  - Uses: Telegram Bot API
```

---

## 📋 Remaining Features to Build

### 4. QR Code Enhancement System

**Architecture:**
```python
# Models
QRCode:
  - code: str (unique QR code)
  - qr_type: str (CUTTER, BIT, SERIAL_UNIT, LOCATION, EMPLOYEE, JOB_CARD, DELIVERY)
  - content_type: ForeignKey
  - object_id: int
  - related_object: GenericForeignKey
  - image: ImageField (generated QR image)
  - created_at, last_scanned_at
  - scan_count
  - is_active

QRScanLog:
  - qr_code: ForeignKey(QRCode)
  - scanned_by_user: ForeignKey(User)
  - scanned_by_employee: ForeignKey(Employee)
  - scanned_at: DateTime
  - location: GPS coordinates
  - device_info: JSON (phone model, OS, app version)
  - scan_context: str (RECEIVING, PRODUCTION, SHIPPING, INVENTORY_CHECK, etc.)
  - metadata: JSON

# Services
QRCodeService:
  - generate_qr(obj, qr_type) -> QRCode
  - scan_qr(code, user, gps=None) -> object
  - verify_qr(code) -> bool
  - track_scan(code, user, context, location)
  - get_scan_history(code)

# Use Cases
- Production: Scan cutter serial → Auto-populate BOM map cell
- Inventory: Scan location → Verify items in that location
- Logistics: Scan package → Track movement, verify delivery address
- Employee: Scan employee badge → Clock in/out, verify identity
- Job Card: Scan job card → View/update status, access digital map
```

### 5. GPS Address Verification System

**Architecture:**
```python
# Models
LocationVerification:
  - verified_object_type: str (DELIVERY, RECEIVING, SHIPPING, INVENTORY_CHECK)
  - content_type: ForeignKey
  - object_id: int
  - related_object: GenericForeignKey

  # Stored address
  expected_latitude: Decimal
  expected_longitude: Decimal
  expected_address: str
  geofence_radius_meters: int (default 100m)

  # Actual GPS
  actual_latitude: Decimal
  actual_longitude: Decimal
  actual_address: str (reverse geocoded)

  # Verification
  distance_meters: float (calculated distance)
  is_within_geofence: bool
  verified_at: DateTime
  verified_by: ForeignKey(User)
  device_accuracy_meters: float

  # Override
  override_allowed: bool
  override_reason: str
  overridden_by: ForeignKey(User)

# Services
GPSVerificationService:
  - verify_location(expected_coords, actual_coords, radius=100) -> bool
  - calculate_distance(lat1, lon1, lat2, lon2) -> meters
  - reverse_geocode(lat, lon) -> address
  - create_geofence(location, radius)
  - log_verification(obj, gps_data, user)

# Use Cases
- Delivery: Verify driver is at correct delivery address
- Receiving: Verify inspector is at receiving dock
- Inventory Check: Verify employee is at physical location
- Asset Tracking: Verify equipment is at reported location
```

### 6. Phone ID Employee Tracking

**Architecture:**
```python
# Models
EmployeeDevice:
  - employee: ForeignKey(HREmployee)
  - device_id: str (unique device identifier)
  - device_type: str (ANDROID, IOS, WEB)
  - device_model: str
  - os_version: str
  - app_version: str

  # Authentication
  is_primary_device: bool
  is_trusted: bool
  registered_at: DateTime
  last_seen_at: DateTime

  # Push notifications
  fcm_token: str (Firebase Cloud Messaging token)

  # Security
  is_active: bool
  deactivated_at: DateTime
  deactivation_reason: str

EmployeeActivity:
  - employee: ForeignKey(HREmployee)
  - device: ForeignKey(EmployeeDevice)
  - activity_type: str (LOGIN, LOGOUT, SCAN_QR, GPS_CHECK, NOTIFICATION_READ, etc.)
  - activity_at: DateTime
  - location_lat, location_lon
  - metadata: JSON

EmployeePresence:
  - employee: ForeignKey(HREmployee)
  - date: Date
  - clock_in_time: DateTime
  - clock_in_location: GPS
  - clock_in_device: ForeignKey(EmployeeDevice)
  - clock_out_time: DateTime
  - clock_out_location: GPS
  - clock_out_device: ForeignKey(EmployeeDevice)
  - total_hours: Decimal
  - is_verified: bool

# Services
DeviceTrackingService:
  - register_device(employee, device_info) -> EmployeeDevice
  - verify_device(device_id) -> Employee
  - get_employee_by_device(device_id) -> Employee
  - update_last_seen(device_id)
  - deactivate_device(device_id, reason)
  - get_active_devices(employee)

# Use Cases
- Auto-login: Identify employee by phone ID
- Clock in/out: Track attendance via phone
- Security: Only allow registered devices
- Location tracking: Know where employees are
- Push targeting: Send notifications to specific devices
```

### 7. REST API Endpoints for Grid Operations

**API Structure:**
```python
# Cutter BOM Grid APIs
GET    /api/bom-grids/                           # List grids
GET    /api/bom-grids/{id}/                      # Get grid detail
POST   /api/bom-grids/                           # Create grid
PUT    /api/bom-grids/{id}/                      # Update grid
DELETE /api/bom-grids/{id}/                      # Delete grid

GET    /api/bom-grids/{id}/cells/                # List cells
POST   /api/bom-grids/{id}/cells/                # Add cell
PUT    /api/bom-grids/{id}/cells/{cell_id}/      # Update cell
DELETE /api/bom-grids/{id}/cells/{cell_id}/      # Delete cell

POST   /api/bom-grids/{id}/cells/validate/       # Validate cell entry
GET    /api/bom-grids/{id}/availability/         # Get availability summary
POST   /api/bom-grids/{id}/assign-sequences/     # Assign sequence numbers
POST   /api/bom-grids/{id}/refresh-summaries/    # Refresh BOM summaries

# Cutter Map APIs
GET    /api/maps/                                # List maps
GET    /api/maps/{id}/                           # Get map detail
POST   /api/maps/                                # Create map
PUT    /api/maps/{id}/                           # Update map

POST   /api/maps/{id}/create-from-bom/           # Initialize from BOM
GET    /api/maps/{id}/validation-summary/        # Get validation state
POST   /api/maps/{id}/validate/                  # Validate entire map
POST   /api/maps/{id}/cells/{cell_id}/set-cutter/  # Set actual cutter

GET    /api/maps/{id}/compare/{other_id}/        # Compare two maps

# Real-time validation
POST   /api/validate-cell-entry/
  Request: {grid_id, cell_id, cutter_type_id}
  Response: {
    is_valid: bool,
    message: str,
    remaining: int,
    availability: {...}
  }

# Approval APIs
GET    /api/approvals/pending/                   # My pending approvals
GET    /api/approvals/requests/                  # All requests I can see
GET    /api/approvals/requests/{id}/             # Request detail
POST   /api/approvals/requests/                  # Create request
POST   /api/approvals/requests/{id}/submit/      # Submit for approval
POST   /api/approvals/steps/{step_id}/approve/   # Approve step
POST   /api/approvals/steps/{step_id}/reject/    # Reject step
POST   /api/approvals/steps/{step_id}/delegate/  # Delegate step

# Notification APIs
GET    /api/notifications/                       # My notifications
GET    /api/notifications/unread/                # Unread count
POST   /api/notifications/{id}/mark-read/        # Mark as read
POST   /api/notifications/mark-all-read/         # Mark all read

GET    /api/announcements/                       # Active announcements
GET    /api/announcements/{id}/                  # Announcement detail
POST   /api/announcements/{id}/mark-read/        # Mark as read

# QR Code APIs
POST   /api/qr/generate/                         # Generate QR code
GET    /api/qr/scan/{code}/                      # Scan QR code
POST   /api/qr/verify/                           # Verify QR code
GET    /api/qr/{code}/history/                   # Scan history

# GPS Verification APIs
POST   /api/gps/verify/                          # Verify location
POST   /api/gps/log-location/                    # Log GPS location
```

### 8. Excel Import/Export

**Implementation:**
```python
# Services
ExcelImportService:
  - import_bom_from_excel(file) -> CutterBOMGridHeader
  - validate_excel_structure(file) -> errors[]
  - parse_excel_cells(worksheet) -> cells[]

ExcelExportService:
  - export_grid_to_excel(grid) -> file
  - export_map_to_excel(map) -> file
  - apply_cell_colors(worksheet, map)
  - generate_print_layout(map) -> file

# Excel Structure for Import
Sheet "Grid Config":
  - Blade Count
  - Max Pockets Per Blade
  - Ordering Scheme
  - Show Reclaimed Cutters

Sheet "Cells":
  | Blade | Pocket | Primary/Secondary | Location | Section | Cutter Type | Formation Order |
  |-------|--------|-------------------|----------|---------|-------------|-----------------|
  | 1     | 1      | P                 | Cone 1   | Cone    | PDC-13-5    | 1               |
  | 1     | 2      | P                 | Cone 2   | Cone    | PDC-13-5    | 2               |

# Excel Structure for Export (Map)
Sheet "Map - {map_type}":
  - Color-coded cells (green=correct, yellow=substituted, red=damaged)
  - Required vs Actual columns
  - Serial numbers
  - Notes columns
  - Validation summary at bottom
```

### 9. Serial Number Scanning Integration

**Implementation:**
```python
# Mobile App Integration
ScannerService:
  - scan_qr_code() -> code
  - scan_barcode() -> code
  - decode_serial_number(code) -> SerialUnit

# Workflow
1. Brazer scans cutter serial number
2. System looks up SerialUnit
3. Validates cutter type matches BOM cell
4. Auto-populates map cell with:
   - Actual cutter type
   - Serial number
   - Timestamp
   - Location (if GPS enabled)
5. Real-time validation check
6. Show green/yellow/red feedback
7. Update available inventory

# API Endpoint
POST /api/scan-serial/
  Request: {
    map_id: int,
    cell_id: int,
    serial_code: str,
    gps_location: {lat, lon} optional
  }
  Response: {
    success: bool,
    serial_unit: {...},
    validation: {is_valid, message, remaining},
    cell_updated: {...}
  }
```

### 10. Map Comparison Tool

**Implementation:**
```python
# Service
MapComparisonService:
  - compare_maps(map1, map2) -> ComparisonResult
  - get_differences(map1, map2) -> []
  - highlight_changes(map1, map2) -> visual_diff

# ComparisonResult
{
  'map1': map_header_1,
  'map2': map_header_2,
  'summary': {
    'total_cells': 50,
    'unchanged': 40,
    'changed': 8,
    'added': 1,
    'removed': 1
  },
  'differences': [
    {
      'cell_reference': 'B1P3P',
      'field': 'actual_cutter_type',
      'map1_value': 'PDC-13-5',
      'map2_value': 'PDC-13-6',
      'change_type': 'SUBSTITUTION'
    },
    ...
  ],
  'substitutions': [...],
  'new_damage': [...],
  'reworked_cells': [...]
}

# UI View
Side-by-side grid comparison:
- Left: As-Built map
- Right: Post-Rework map
- Highlight differences in color
- Click cell to see change details
- Filter by change type
- Export comparison report
```

### 11. Print-Optimized Layouts

**Implementation:**
```python
# Template Engine
PrintLayoutService:
  - generate_job_card_pdf(map) -> PDF
  - generate_brazer_worksheet(map) -> PDF
  - generate_qc_checklist(map) -> PDF

# PDF Structure (Job Card)
┌─────────────────────────────────────┐
│ Job Card: JC-001                    │
│ Bit Design: HP-X123-M2              │
│ QR Code: [███]  ← Link to digital   │
├─────────────────────────────────────┤
│ Cutter Map - As-Built               │
│                                     │
│ Blade 1:                            │
│ ┌──┬──┬──┬──┐                      │
│ │C1│C2│C3│C4│  ← Color-coded       │
│ │🟢│🟢│🟡│🟢│                      │
│ └──┴──┴──┴──┘                      │
│                                     │
│ Legend:                             │
│ 🟢 Correct   🟡 Substituted         │
│ 🔴 Damaged   ⚪ Empty               │
│                                     │
│ Notes:                              │
│ - C3 substituted: PDC-13-6          │
│   instead of PDC-13-5               │
│                                     │
│ Brazer: ____________ Date: ______   │
│ Inspector: _________ Date: ______   │
└─────────────────────────────────────┘

# Features:
- Large fonts for readability
- Color-coded cells
- QR code linking to digital map
- Checkboxes for manual verification
- Notes section
- Signature lines
- Multiple layouts (portrait/landscape)
- Optimized for A4/Letter paper
```

---

## 🔧 Technical Stack

### Backend
- **Django 5.2.6** - Web framework
- **PostgreSQL** - Database
- **Django REST Framework** - API
- **Celery** - Async tasks (for notifications)
- **Redis** - Caching, Celery broker

### Notifications
- **Twilio** - WhatsApp & SMS
- **SendGrid/SMTP** - Email
- **Firebase Cloud Messaging** - Push notifications
- **Telegram Bot API** - Telegram messages

### QR Codes
- **qrcode** - QR generation
- **Pillow** - Image processing
- **pyzbar** - QR scanning (mobile)

### GPS
- **geopy** - Geocoding, distance calculation
- **django-geoposition** - GPS fields

### Excel
- **openpyxl** - Excel read/write
- **xlsxwriter** - Excel generation with formatting

### PDF
- **reportlab** - PDF generation
- **weasyprint** - HTML to PDF (styled layouts)

---

## 📊 Database Schema Extensions

### Notification Tables
```sql
notifications_channel
notifications_template
notifications_preference
notifications_notification
notifications_delivery
notifications_announcement
notifications_announcement_read
```

### Approval Tables
```sql
approvals_workflow
approvals_level
approvals_request
approvals_step
approvals_history
approvals_delegation
```

### QR Code Tables (New)
```sql
qr_codes_qrcode
qr_codes_scanlog
```

### GPS Tables (New)
```sql
gps_location_verification
```

### Device Tracking Tables (New)
```sql
devices_employee_device
devices_employee_activity
devices_employee_presence
```

---

## 🚀 Implementation Priority

### Phase 1: Foundation (Current)
✅ Notification models
✅ Approval models
⏳ Notification services
⏳ Approval services

### Phase 2: Core Features
- QR code system
- GPS verification
- Phone ID tracking
- REST APIs

### Phase 3: Enhancements
- Excel import/export
- Serial scanning
- Map comparison
- Print layouts

### Phase 4: Polish
- Mobile app
- WebSocket real-time
- Analytics dashboard
- Reporting

---

## 💬 Integration Examples

### Example 1: Brazer Workflow with All Systems
```
1. Brazer arrives at workstation
   → Phone ID identifies him (EmployeeDevice)
   → GPS verifies he's at correct location (GPSVerification)
   → Clock-in recorded (EmployeePresence)

2. Scans job card QR code
   → QR system loads digital map (QRCode)
   → Map displayed on tablet/phone

3. Scans cutter serial number
   → Serial lookup (SerialUnit)
   → Auto-populates cell (CutterMapCell)
   → Real-time validation (CutterBOMValidator)
   → Check availability (CutterAvailabilityService)

4. Needs substitution approval
   → Creates approval request (ApprovalRequest)
   → Notifications sent to supervisor (Notification)
   → WhatsApp message sent
   → Supervisor approves on phone
   → Approval notification back to brazer

5. Completes stage
   → Map validation (CutterMapValidator)
   → QC notified (Announcement)
   → Status update visible to all (visibility controls)
```

### Example 2: Stock Check with GPS
```
1. Inspector opens stock check task
2. System shows expected location
3. Inspector's phone GPS captures current location
4. GPS verification checks:
   - Distance from expected location
   - Within geofence?
   - Accuracy acceptable?
5. If OK: Allow stock count entry
6. If NOT OK: Warning + option to override with reason
7. QR scan each item to verify
8. Results logged with GPS proof
```

### Example 3: Delivery Verification
```
1. Driver receives delivery task
2. Task shows delivery address + map
3. Driver arrives, app captures GPS
4. System verifies GPS matches delivery address
5. If match: Allow "Delivered" button
6. Customer scans QR to confirm receipt
7. Both GPS + QR scan create proof of delivery
8. Automatic notification to sender
9. Invoice triggered
```

---

## 📱 Mobile App Features

### For Production Workers (Brazers, Operators)
- QR code scanner
- Digital job cards
- Cutter BOM maps
- Real-time validation feedback
- Clock in/out
- Notifications
- GPS auto-capture

### For Inspectors (QC, NDT)
- Inspection checklists
- Photo capture
- GPS verification
- Approval submission
- Result entry

### For Supervisors
- Approval actions (approve/reject from phone)
- Team location view
- Notifications
- Dashboard

### For Logistics
- Delivery tracking
- GPS verification
- Package scanning
- Proof of delivery

---

## 🔐 Security Considerations

### Device Registration
- Only registered devices can access
- Two-factor authentication option
- Device deactivation on loss

### GPS Spoofing Prevention
- Check GPS accuracy
- Require device accuracy < 20m
- Log suspicious patterns
- Manual override with approval

### QR Code Security
- Codes expire after use (optional)
- Encrypted QR data
- Scan logging
- Rate limiting

### API Security
- JWT authentication
- Permission-based access
- Rate limiting
- Audit logging

---

**This is the complete architecture. Shall I continue building the remaining services and APIs?**

# Floor Management System - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [HR & Administration](#hr--administration)
4. [Inventory Management](#inventory-management)
5. [Engineering](#engineering)
6. [Production](#production)
7. [Quality Management](#quality-management)
8. [Planning & KPI](#planning--kpi)
9. [Sales & Lifecycle](#sales--lifecycle)
10. [Common Tasks](#common-tasks)

## Getting Started

### Logging In
1. Navigate to the system URL in your web browser
2. Enter your username and password
3. Click "Login"

### Dashboard Overview
After logging in, you'll see the main dashboard with:
- Quick access cards to all modules
- Recent activity summary
- Key performance indicators
- Notifications and alerts

### Navigation
- **Sidebar**: Access all modules from the left sidebar
- **Top Bar**: User profile, notifications, and search
- **Breadcrumbs**: Track your location in the system

## HR & Administration

### Employee Management

#### Adding a New Employee
1. Navigate to **HR & Admin** → **Employees**
2. Click **New Employee**
3. Fill in the wizard:
   - **Personal Information**: Name, ID, contact details
   - **Employment Details**: Department, position, hire date
   - **Contract Information**: Type, dates, compensation
   - **Work Schedule**: Days, hours, shift pattern
4. Click **Save**

#### Viewing Employee Details
1. Go to **HR & Admin** → **Employees**
2. Search or browse for the employee
3. Click on the employee name
4. View comprehensive profile including:
   - Personal information
   - Employment details
   - Contracts and compensation
   - Work schedules
   - **QR Code** for identification

#### Downloading Employee QR Code
1. Open employee detail page
2. Scroll to **QR Code** section
3. Click **Download QR Code** or **Print QR Code**
4. Use for employee badges or identification

### Contract Management

#### Creating a Contract
1. Go to **HR & Admin** → **Contracts**
2. Click **New Contract**
3. Fill in contract details:
   - Employee
   - Contract type (Full-time, Part-time, etc.)
   - Start and end dates
   - Compensation details
4. Save contract

### Shift Management

#### Creating Shift Templates
1. Navigate to **HR & Admin** → **Shifts**
2. Click **New Shift Template**
3. Define:
   - Shift name and code
   - Start and end times
   - Days of week
4. Save template

#### Assigning Shifts to Employees
1. Go to **HR & Admin** → **Shift Assignments**
2. Click **New Assignment**
3. Select employee and shift template
4. Set effective dates
5. Save assignment

### Asset Management

#### Adding Company Assets
1. Go to **HR & Admin** → **Assets**
2. Click **New Asset**
3. Enter asset details:
   - Asset type (laptop, vehicle, phone, etc.)
   - Name and tag number
   - Serial number
   - Purchase information
4. Save asset

#### Assigning Assets to Employees
1. Open asset detail page
2. Click **Assign to Employee**
3. Select employee
4. Set assignment date
5. Confirm assignment

#### Returning Assets
1. Navigate to assigned asset
2. Click **Return Asset**
3. Enter return date and condition
4. Save return record

## Employee Portal

### Accessing the Portal
1. Log in with employee credentials
2. Click **Employee Portal** or navigate to `/portal/`

### Submitting Leave Requests
1. In portal, go to **My Leave**
2. Click **Submit Leave Request**
3. Fill in:
   - Leave type (Annual, Sick, etc.)
   - Start and end dates
   - Reason
4. Submit request
5. **Automatic notification** sent to manager

### Tracking Leave Requests
1. Go to **My Requests**
2. View status of all requests:
   - Pending
   - Approved
   - Rejected
3. Click on request to view details

## Inventory Management

### Item Master

#### Adding Items
1. Navigate to **Inventory** → **Items**
2. Click **New Item**
3. Enter item details:
   - SKU and name
   - Category
   - Unit of measure
   - Specifications
4. Save item

### Stock Management

#### Viewing Stock Levels
1. Go to **Inventory** → **Stock**
2. View all stock locations
3. Use filters to find specific items
4. Check quantity on hand

#### Stock Adjustments
1. Navigate to **Inventory** → **Stock Adjustments**
2. Click **New Adjustment**
3. Select item and location
4. Enter new quantity
5. Provide reason
6. Save adjustment

### Serial Units

#### Tracking Serial Numbers
1. Go to **Inventory** → **Serial Units**
2. View all serialized items
3. Track location and status
4. View movement history

## Engineering

### Bit Design Management

#### Creating a Bit Design
1. Navigate to **Engineering** → **Bit Designs**
2. Click **New Design**
3. Enter design information:
   - Design code
   - Type and level
   - Size and specifications
4. Save design

#### Creating Design Revisions
1. Open bit design detail page
2. Click **New Revision**
3. Enter revision details:
   - Revision number
   - Change notes
   - Effective date
4. Save revision

### Bill of Materials (BOM)

#### Creating a BOM
1. Go to **Engineering** → **BOMs**
2. Click **New BOM**
3. Select bit design revision
4. Enter BOM details
5. Add BOM lines through admin interface
6. Save BOM

#### Viewing BOM Details
1. Navigate to **Engineering** → **BOMs**
2. Click on BOM number
3. View:
   - Header information
   - All BOM lines with quantities
   - Associated bit design
4. Export or print BOM

## Production

### Job Cards

#### Creating a Job Card
1. Go to **Production** → **Job Cards**
2. Click **New Job Card**
3. Fill in details:
   - Serial unit
   - Job type (New, Repair, etc.)
   - Customer information
4. Save job card

#### Routing and Operations
1. Open job card detail
2. Add routing steps
3. Assign operations
4. Track progress through production

### Batch Orders

#### Creating Batches
1. Navigate to **Production** → **Batches**
2. Click **New Batch**
3. Define batch parameters
4. Add items to batch
5. Start production

## Quality Management

### Non-Conformance Reports (NCR)

#### Creating an NCR
1. Go to **Quality** → **NCRs**
2. Click **New NCR**
3. Document:
   - Issue description
   - Affected items
   - Severity
4. Add analysis and corrective actions
5. Track to closure

### Calibration Management

#### Equipment Calibration
1. Navigate to **Quality** → **Calibration**
2. View due calibrations
3. Record calibration results
4. Update equipment status

## Planning & KPI

### KPI Dashboard

#### Viewing KPIs
1. Go to **Planning** → **KPI Dashboard**
2. View all defined KPIs
3. See current values and trends
4. Drill down for details

#### Adding KPI Values
1. Navigate to **Planning** → **KPIs**
2. Select KPI definition
3. Click **Add Value**
4. Enter date and value
5. Save

### Production Scheduling

#### Creating Schedules
1. Go to **Planning** → **Schedules**
2. Click **New Schedule**
3. Define schedule parameters
4. Assign resources
5. Publish schedule

## Sales & Lifecycle

### Customer Management

#### Adding Customers
1. Navigate to **Sales** → **Customers**
2. Click **New Customer**
3. Enter customer details
4. Save customer record

### Bit Lifecycle Tracking

#### Tracking Bit Usage
1. Go to **Sales** → **Lifecycle**
2. View timeline of bit usage
3. Track:
   - Delivery to customer
   - Time at rig
   - Dull grading
   - Return for repair
4. Analyze performance

## Common Tasks

### Searching
1. Use the search bar in the top navigation
2. Enter keywords
3. Filter by module if needed
4. Click on results to navigate

### Filtering Lists
1. On any list page, use filter options
2. Select criteria from dropdowns
3. Click **Filter** or **Search**
4. Clear filters to reset

### Exporting Data
1. On list pages, look for **Export** button
2. Choose format (CSV, PDF, Excel)
3. Download file
4. Open in appropriate application

### Printing
1. Navigate to detail page
2. Use browser print function (Ctrl+P / Cmd+P)
3. Or click **Print** button if available
4. Select printer and options

### QR Code Scanning
1. Use QR scanner app on mobile device
2. Scan employee or asset QR code
3. Automatically redirected to detail page
4. View full information

## Notifications

### Viewing Notifications
1. Click bell icon in top bar
2. View unread notifications
3. Click to view details
4. Mark as read

### Notification Types
- **Leave Requests**: New submissions, approvals, rejections
- **System Alerts**: Important updates
- **Task Reminders**: Due dates and deadlines
- **Approvals**: Items requiring your action

## User Profile

### Updating Profile
1. Click your name in top bar
2. Select **Profile**
3. Update information:
   - Contact details
   - Password
   - Preferences
4. Save changes

### Changing Password
1. Go to **Profile** → **Change Password**
2. Enter current password
3. Enter new password (twice)
4. Save

## Tips and Best Practices

### Data Entry
- Fill all required fields (marked with *)
- Use consistent formats for dates and numbers
- Double-check before saving
- Use search to avoid duplicates

### Navigation
- Use breadcrumbs to track location
- Bookmark frequently used pages
- Use keyboard shortcuts where available

### Performance
- Limit search results with filters
- Export large datasets rather than viewing all
- Close unused browser tabs

### Security
- Log out when finished
- Don't share credentials
- Report suspicious activity
- Change password regularly

## Getting Help

### In-App Help
- Look for **?** icons for field help
- Hover over labels for tooltips
- Check validation messages for errors

### Support Resources
- **User Manual**: This guide
- **Admin Guide**: `docs/ADMIN_GUIDE.md`
- **FAQ**: Common questions and answers
- **Support**: Contact your system administrator

## Keyboard Shortcuts

- `Ctrl+S` or `Cmd+S`: Save form (where applicable)
- `Ctrl+F` or `Cmd+F`: Search within page
- `Esc`: Close modal dialogs
- `Tab`: Navigate between form fields

## Troubleshooting

### Can't Find an Item
1. Clear all filters
2. Check spelling in search
3. Try broader search terms
4. Contact administrator if item should exist

### Permission Denied
- Contact your supervisor or administrator
- You may need additional permissions
- Some features are role-restricted

### Data Not Saving
- Check for required fields
- Look for validation errors in red
- Ensure stable internet connection
- Try refreshing and re-entering

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-23
**For System Version**: 1.0.0

# Knowledge & Instructions Module

A comprehensive knowledge management and business rules engine for the Floor Management System.

## Overview

This module provides:

1. **Knowledge Center** - Centralized repository for procedures, guidelines, policies, and documentation
2. **Dynamic Instruction Engine** - Powerful rule system that evaluates conditions and triggers actions automatically
3. **Training Center** - Learning management system integrated with HR qualifications
4. **Document Management** - File storage and attachment system
5. **FAQ System** - Frequently asked questions management

## Key Features

### 1. Knowledge Articles

- **Multiple Types**: Procedures, Work Instructions, Guidelines, Policies, FAQs, Checklists, Templates, Safety Documents, Quality Documents
- **Workflow**: Draft → In Review → Approved → Published → Archived
- **Versioning**: Track changes with version history
- **Rich Content**: HTML/Markdown body with attachments
- **Tagging & Categories**: Hierarchical organization
- **Access Control**: Restrict by department or position
- **Acknowledgment**: Require users to acknowledge reading
- **Review Tracking**: Automatic alerts for documents needing review

### 2. Dynamic Instruction Engine (THE POWER!)

The instruction engine allows you to define business rules that automatically evaluate and trigger actions.

#### How It Works:

1. **Define Conditions** - Select ANY model and ANY field to check
2. **Set Operators** - Equals, Contains, Greater Than, Between, Regex, etc.
3. **Configure Actions** - What happens when conditions are met
4. **Set Scope** - Where the rule applies (default, temporary, specific customer, etc.)

#### Example Instructions:

```
IF bit.smi_type == "PDC" AND bit.size > 8.5
THEN:
  - Show Warning: "Use undercut gauge by 0.25"
  - Set Field: gauge_undercut = 0.25
  - Log Audit Entry

IF serial.customer.name == "ARAMCO" AND operation.type == "QC"
THEN:
  - Require Approval
  - Send Email to QC Manager
  - Show Info: "Apply ARAMCO QC standards"

IF serial.backloaded == True
THEN:
  - Show Critical Warning: "DO NOT WASH - Serial is backloaded"
  - Prevent Action: wash_operation
  - Create Notification for Supervisor
```

#### Supported Conditions:

- **Target ANY Model**: HREmployee, BitDesign, JobCard, Customer, Operation, etc.
- **Field Paths**: Nested fields like `customer__region__name` or `bit_design__smi_type`
- **Operators**: EQUALS, NOT_EQUALS, GREATER_THAN, LESS_THAN, CONTAINS, STARTS_WITH, IN_LIST, REGEX, BETWEEN, IS_NULL, etc.
- **Logic**: AND/OR with parenthetical grouping
- **Case Sensitivity**: Optional case-sensitive matching

#### Supported Actions:

**Display Actions:**
- SHOW_MESSAGE - Display informational toast/alert
- SHOW_WARNING - Display warning message
- SHOW_ERROR - Display blocking error (prevents action)
- SHOW_INFO - Display information panel

**Control Actions:**
- PREVENT_ACTION - Block the current operation
- REQUIRE_CONFIRMATION - User must confirm to proceed
- REQUIRE_APPROVAL - Requires manager/supervisor approval
- REQUIRE_OVERRIDE - Requires manager override with reason

**Notification Actions:**
- SEND_EMAIL - Send email to specified users/roles
- SEND_SMS - Send SMS notification
- CREATE_NOTIFICATION - Create in-app notification

**Data Modification Actions:**
- SET_FIELD_VALUE - Automatically set a field value
- CALCULATE_VALUE - Calculate and suggest a value
- INCREMENT_COUNTER - Increment a counter field

**Workflow Actions:**
- CHANGE_STATUS - Automatically change object status
- ASSIGN_TO_USER - Assign task to specific user
- CREATE_TASK - Create a work order or task

**Validation Actions:**
- VALIDATE_FIELD - Custom field validation
- ENFORCE_MINIMUM - Ensure minimum value
- ENFORCE_MAXIMUM - Ensure maximum value
- ENFORCE_PATTERN - Validate against regex pattern

**UI Actions:**
- HIGHLIGHT_FIELD - Highlight a field in the UI
- DISABLE_FIELD - Disable a field
- HIDE_FIELD / SHOW_FIELD - Control field visibility

**Logging Actions:**
- LOG_AUDIT - Create audit trail entry
- LOG_CUSTOM - Log custom event

#### Instruction Scoping:

Instructions can be scoped to:
- **Default**: Always applies
- **Temporary**: Time-limited (valid_from to valid_until)
- **Specific Entity**: Only for certain customer, bit design, serial, etc.
- **Department/Position**: Only for certain roles
- **Include/Exclude**: Inclusive or exclusive scope

### 3. Training Center

Complete learning management system:

- **Courses**: Structured learning paths with lessons
- **Lesson Types**: Video, Reading, Interactive, Quiz, Practical, Assignment
- **Progress Tracking**: Track completion per lesson
- **Assessments**: Quizzes with passing scores
- **Certificates**: Auto-generate on completion
- **HR Integration**: Automatically grants HR Qualifications upon completion
- **Scheduled Sessions**: For instructor-led training
- **Mandatory Training**: Enforce required courses by position/department

### 4. Document Management

- **File Types**: PDF, Image, Video, Audio, Spreadsheet, CAD, etc.
- **Versioning**: Track document versions
- **Metadata**: Checksums, MIME types, expiry dates
- **Download Tracking**: Count downloads
- **Public/Private**: Control access
- **Generic Attachments**: Attach to articles, instructions, lessons

### 5. FAQ System

- **Grouped FAQs**: Organize by topic
- **Rich Answers**: HTML/Markdown support
- **Keywords**: Enhanced search
- **Helpfulness Tracking**: Was this helpful? metrics
- **Featured FAQs**: Highlight important questions

## Architecture

```
floor_app/operations/knowledge/
├── models/
│   ├── article.py      # Knowledge articles & attachments
│   ├── category.py     # Hierarchical categories
│   ├── document.py     # File storage
│   ├── faq.py          # FAQ groups & entries
│   ├── instruction.py  # RULE ENGINE (conditions, actions, scopes)
│   ├── tag.py          # Tagging system
│   └── training.py     # Courses, lessons, enrollments
├── services/
│   ├── rule_engine.py      # Core rule evaluation & execution
│   ├── knowledge_service.py # Article business logic
│   └── training_service.py  # Training operations
├── views/
│   ├── articles.py     # CRUD for articles
│   ├── instructions.py # Rule management
│   ├── training.py     # Training center
│   ├── dashboard.py    # Main dashboard
│   └── ...
├── forms/              # Django forms
├── admin.py           # Comprehensive admin interface
├── urls.py            # URL routing
├── signals.py         # Automatic rule evaluation hooks
└── templates/         # Frontend templates
```

## Integration with Other Modules

### HR Module

- Articles can be owned by HR Departments
- Training courses target specific HR Positions
- Courses grant HR Qualifications upon completion
- Instructions can target employees by department/position

### Future Modules (Inventory, Production, Quality)

The instruction engine uses **GenericForeignKey** for maximum flexibility:

```python
# When you add BitDesign model later:
class InstructionTargetScope(models.Model):
    target_content_type = models.ForeignKey(ContentType, ...)
    target_object_id = models.PositiveBigIntegerField(...)
    target = GenericForeignKey(...)

# Instruction can target ANY model:
scope.target_content_type = ContentType.objects.get_for_model(BitDesign)
scope.target_object_id = 123
# Now instruction applies to BitDesign #123
```

## Usage Examples

### Creating a Knowledge Article

```python
from floor_app.operations.knowledge.models import Article, Category

article = Article.objects.create(
    code='PROC-QC-001',
    title='NDT Inspection Procedure',
    summary='Standard procedure for non-destructive testing',
    body='<h2>Purpose</h2>...',
    article_type=Article.ArticleType.PROCEDURE,
    status=Article.Status.DRAFT,
    priority=Article.Priority.HIGH,
    category=Category.objects.get(name='Quality'),
)
```

### Creating an Instruction Rule

```python
from floor_app.operations.knowledge.models import InstructionRule, RuleCondition, RuleAction
from django.contrib.contenttypes.models import ContentType

# Create the instruction
instruction = InstructionRule.objects.create(
    code='INS-PDC-001',
    title='Undercut Gauge for Large PDC Bits',
    description='When PDC bit size exceeds 8.5 inches, automatically apply gauge undercut',
    instruction_type=InstructionRule.InstructionType.TECHNICAL,
    priority=InstructionRule.Priority.HIGH,
    status=InstructionRule.Status.ACTIVE,
    is_default=True,
)

# Add condition (when BitDesign exists)
# ct = ContentType.objects.get(app_label='inventory', model='bitdesign')
# RuleCondition.objects.create(
#     instruction=instruction,
#     target_model=ct,
#     field_path='size',
#     operator=RuleCondition.Operator.GREATER_THAN,
#     value='8.5',
# )

# Add action
RuleAction.objects.create(
    instruction=instruction,
    action_type=RuleAction.ActionType.SHOW_WARNING,
    message_template='Apply gauge undercut of 0.25 for bits larger than 8.5"',
    severity='warning',
)
```

### Evaluating Rules

```python
from floor_app.operations.knowledge.services import RuleEngine
from django.contrib.contenttypes.models import ContentType

# Build context with objects to evaluate
ct_bit = ContentType.objects.get_for_model(BitDesign)
context = {
    ct_bit.id: bit_design_instance,
}

# Evaluate
engine = RuleEngine(user=request.user, request=request)
results = engine.evaluate_for_context(context, trigger_event='save')

# Check results
if results['prevented']:
    # Action was blocked
    pass

if results['requires_confirmation']:
    # Show confirmation dialog
    pass

for action in results['actions']:
    # Process each action result
    pass
```

### Enrolling in Training

```python
from floor_app.operations.knowledge.services import TrainingService

enrollment, created = TrainingService.enroll_employee(
    course=course,
    employee=employee,
    enrolled_by=request.user
)

# Complete a lesson
TrainingService.complete_lesson(enrollment, lesson, quiz_score=85.0)

# Get employee training dashboard
dashboard = TrainingService.get_employee_training_dashboard(employee)
```

## URLs

- `/knowledge/` - Main dashboard
- `/knowledge/articles/` - Article list
- `/knowledge/articles/<slug>/` - Article detail
- `/knowledge/instructions/` - Instruction rules list
- `/knowledge/instructions/<code>/` - Instruction detail
- `/knowledge/training/` - Training dashboard
- `/knowledge/training/courses/` - Course catalog
- `/knowledge/training/my-courses/` - User's enrollments
- `/knowledge/faq/` - FAQ list
- `/knowledge/documents/` - Document library
- `/knowledge/search/` - Global search

## Admin Interface

Access at `/admin/knowledge/`:

- **InstructionRule** - Create/edit business rules with inline conditions and actions
- **Article** - Manage knowledge articles with workflow
- **TrainingCourse** - Create courses with lessons
- **Document** - Upload and manage files
- **Category/Tag** - Organize content

## Permissions

- `knowledge.add_article` - Create articles
- `knowledge.change_article` - Edit articles
- `knowledge.can_publish_article` - Publish articles
- `knowledge.can_approve_article` - Approve articles
- `knowledge.add_instructionrule` - Create instructions
- `knowledge.can_activate_instruction` - Activate/deactivate rules
- `knowledge.add_trainingcourse` - Create courses
- `knowledge.can_publish_course` - Publish courses
- `knowledge.can_enroll_others` - Enroll other employees

## Future Enhancements

1. **Rich Text Editor** - Add CKEditor or TinyMCE for body fields
2. **API Endpoints** - REST API with Django REST Framework
3. **Mobile App Integration** - API for mobile learning
4. **Advanced Analytics** - Training completion trends, instruction effectiveness
5. **Bulk Operations** - Bulk enroll, bulk publish
6. **Import/Export** - Import articles from external sources
7. **Notifications** - Email/SMS notifications for training reminders
8. **QR Integration** - Scan QR to fetch relevant instructions
9. **Version Comparison** - Side-by-side article version diff
10. **Approval Workflows** - Configurable approval chains

## Testing

Run tests:
```bash
python manage.py test floor_app.operations.knowledge
```

## Migration

Create and apply migrations:
```bash
python manage.py makemigrations knowledge
python manage.py migrate
```

## Dependencies

- Django 5.2+
- PostgreSQL (for JSON fields, indexes)
- Existing HR module (for department, position, employee integration)

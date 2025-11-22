# Requirements System Implementation Guide

## Overview

The Requirements System tracks prerequisites needed to complete job cards, ensuring all necessary data, documents, materials, instructions, and approvals are in place before work proceeds.

## Models Architecture

### 1. RequirementCategory
Defines requirement types with visual styling and display order.

**Standard Categories:**
- `DATA` - Required data/information
- `DOCUMENT` - Required documents/drawings
- `MATERIAL` - Required materials/items
- `INSTRUCTION` - Required instructions/procedures
- `APPROVAL` - Required approvals/sign-offs
- `TOOL_EQUIPMENT` - Required tools/equipment
- `INSPECTION` - Required inspections
- `PERSONNEL` - Required personnel/skills

### 2. RequirementTemplate
Auto-applies requirements to matching job cards based on filters.

**Applicability Filters:**
- Job types (NEW_BIT, REPAIR, RETROFIT, RETROFIT_RECLAIM, SCRAP, REGRIND)
- Customer codes
- MAT levels (0-5)
- Bit size ranges

### 3. JobRequirement
Individual requirement instances with lifecycle tracking.

**Status Flow:**
```
NOT_STARTED → IN_PROGRESS → COMPLETED
                  ↓
            WAITING_DEPENDENCY
                  ↓
               BLOCKED
```

Alternative outcomes: `WAIVED`, `FAILED`

### 4. TechnicalInstruction
Procedures/instructions with smart matching to job cards.

**Matching Priority:**
1. Serial number (most specific)
2. MAT number
3. Job type
4. Customer
5. ALL (global instructions)

---

## Setup: Initial Data Population

### Step 1: Create Requirement Categories

```python
from floor_app.operations.planning.models import RequirementCategory

# Create standard categories
categories = [
    {
        'code': 'DATA',
        'name': 'Required Data',
        'icon': 'fas fa-database',
        'color_hex': '#3498db',
        'display_order': 10
    },
    {
        'code': 'DOCUMENT',
        'name': 'Required Documents',
        'icon': 'fas fa-file-alt',
        'color_hex': '#2ecc71',
        'display_order': 20
    },
    {
        'code': 'MATERIAL',
        'name': 'Required Materials',
        'icon': 'fas fa-box',
        'color_hex': '#e74c3c',
        'display_order': 30
    },
    {
        'code': 'INSTRUCTION',
        'name': 'Required Instructions',
        'icon': 'fas fa-clipboard-list',
        'color_hex': '#f39c12',
        'display_order': 40
    },
    {
        'code': 'APPROVAL',
        'name': 'Required Approvals',
        'icon': 'fas fa-check-circle',
        'color_hex': '#9b59b6',
        'display_order': 50
    },
    {
        'code': 'TOOL_EQUIPMENT',
        'name': 'Required Tools/Equipment',
        'icon': 'fas fa-tools',
        'color_hex': '#34495e',
        'display_order': 60
    },
    {
        'code': 'INSPECTION',
        'name': 'Required Inspections',
        'icon': 'fas fa-search',
        'color_hex': '#16a085',
        'display_order': 70
    },
    {
        'code': 'PERSONNEL',
        'name': 'Required Personnel',
        'icon': 'fas fa-users',
        'color_hex': '#d35400',
        'display_order': 80
    },
]

for cat_data in categories:
    RequirementCategory.objects.get_or_create(
        code=cat_data['code'],
        defaults=cat_data
    )
```

### Step 2: Create Requirement Templates

```python
from floor_app.operations.planning.models import RequirementTemplate, RequirementCategory

# Example: All jobs need bit serial number data
RequirementTemplate.objects.create(
    category=RequirementCategory.objects.get(code='DATA'),
    name='Bit Serial Number',
    description='Bit serial number must be entered and validated',
    applies_to_job_types=['NEW_BIT', 'REPAIR', 'RETROFIT', 'RETROFIT_RECLAIM'],
    is_mandatory=True,
    is_blocking=True,
    display_order=10,
    validation_rules={
        'field': 'serial_unit',
        'required': True,
        'message': 'Serial number is required for this job type'
    }
)

# Example: Repairs need customer approval
RequirementTemplate.objects.create(
    category=RequirementCategory.objects.get(code='APPROVAL'),
    name='Customer Repair Authorization',
    description='Customer must approve repair quotation before work begins',
    applies_to_job_types=['REPAIR'],
    is_mandatory=True,
    is_blocking=True,
    display_order=50,
    validation_rules={
        'check': 'quotation_approved',
        'message': 'Customer must approve quotation before repair work starts'
    }
)

# Example: High-value jobs need engineering review
RequirementTemplate.objects.create(
    category=RequirementCategory.objects.get(code='APPROVAL'),
    name='Engineering Review',
    description='Engineering must review and approve work plan',
    applies_to_job_types=['RETROFIT', 'RETROFIT_RECLAIM'],
    applies_to_mat_level_min=3,  # MAT level 3+
    is_mandatory=True,
    is_blocking=True,
    display_order=20
)

# Example: ENO customers need special inspection
RequirementTemplate.objects.create(
    category=RequirementCategory.objects.get(code='INSPECTION'),
    name='ENO Quality Inspection',
    description='Additional quality inspection required for ENO customers',
    applies_to_customers='ENO',
    is_mandatory=True,
    is_blocking=False,  # Not blocking, but tracked
    display_order=10
)

# Example: Large bits need special equipment
RequirementTemplate.objects.create(
    category=RequirementCategory.objects.get(code='TOOL_EQUIPMENT'),
    name='Heavy Duty Brazing Furnace',
    description='Large bits require HD furnace for proper heat treatment',
    applies_to_bit_size_min=17.5,  # 17.5" and larger
    is_mandatory=True,
    is_blocking=True,
    display_order=30
)
```

### Step 3: Create Technical Instructions

```python
from floor_app.operations.planning.models import TechnicalInstruction

# Global instruction (applies to ALL)
TechnicalInstruction.objects.create(
    instruction_code='SAFETY-001',
    title='General Safety Procedures',
    description='Safety procedures for all shop floor operations',
    instruction_text='''
# General Safety Procedures

1. Wear appropriate PPE at all times
2. Ensure proper ventilation before brazing
3. Check equipment before use
4. Report any safety concerns immediately
    ''',
    applies_to='ALL',
    is_active=True,
    display_order=10
)

# Job type specific
TechnicalInstruction.objects.create(
    instruction_code='BRAZE-REPAIR',
    title='Brazing Procedures for Repair Jobs',
    description='Step-by-step brazing procedures for cutter replacement',
    instruction_text='''
# Brazing Repair Procedures

## Pre-Brazing
1. Clean all surfaces thoroughly
2. Apply flux evenly
3. Pre-heat to 400°F

## Brazing
1. Heat to 1350°F ± 25°F
2. Apply brazing alloy
3. Maintain temperature for 3-5 minutes

## Post-Brazing
1. Cool slowly to room temperature
2. Clean excess flux
3. Visual inspection for gaps
    ''',
    applies_to='JOB_TYPE',
    job_type='REPAIR',
    is_active=True,
    display_order=20
)

# MAT-specific instruction
TechnicalInstruction.objects.create(
    instruction_code='MAT-HVY-001',
    title='Heavy Wall Bit Special Instructions',
    description='Additional procedures for heavy wall bits (MAT >= 4)',
    instruction_text='''
# Heavy Wall Bit Procedures

These bits require extended heat cycles:
- Pre-heat: 2 hours at 400°F
- Brazing: 1450°F for 8-10 minutes
- Post-heat: Hold at 600°F for 1 hour
    ''',
    applies_to='MAT',
    mat_number='HVY',  # Partial match
    is_active=True,
    display_order=30
)

# Customer-specific instruction
TechnicalInstruction.objects.create(
    instruction_code='CUST-ENO-QC',
    title='ENO Customer QC Requirements',
    description='Additional quality requirements for ENO',
    instruction_text='''
# ENO Quality Requirements

1. Document all cutter replacements with photos
2. Complete ENO-specific inspection checklist
3. Package with ENO certification paperwork
4. Ship with tracking and signature required
    ''',
    applies_to='CUSTOMER',
    customer_code='ENO',
    is_active=True,
    display_order=40
)
```

---

## Integration: Auto-Populate Requirements on Job Card Creation

### In `JobCard.save()` or Signal

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from floor_app.operations.production.models import JobCard
from floor_app.operations.planning.models import RequirementTemplate, JobRequirement

@receiver(post_save, sender=JobCard)
def auto_populate_requirements(sender, instance, created, **kwargs):
    """
    Auto-populate requirements from templates when job card is created.
    """
    if not created:
        return  # Only on creation

    job_card = instance

    # Get all applicable templates
    templates = RequirementTemplate.objects.filter(is_active=True)

    for template in templates:
        if template.applies_to_job_card(job_card):
            # Create requirement instance
            JobRequirement.objects.create(
                job_card=job_card,
                category=template.category,
                name=template.name,
                description=template.description,
                is_mandatory=template.is_mandatory,
                is_blocking=template.is_blocking,
                validation_rules=template.validation_rules,
                display_order=template.display_order,
                status='NOT_STARTED',
                source_template=template
            )
```

### Custom Method on JobCard Model

Add to `floor_app/operations/production/models/job_card.py`:

```python
def populate_requirements(self):
    """
    Manually trigger requirement population.
    Useful if templates are updated after job card creation.
    """
    from floor_app.operations.planning.models import RequirementTemplate, JobRequirement

    templates = RequirementTemplate.objects.filter(is_active=True)
    created_count = 0

    for template in templates:
        if template.applies_to_job_card(self):
            # Check if requirement already exists
            existing = JobRequirement.objects.filter(
                job_card=self,
                source_template=template
            ).exists()

            if not existing:
                JobRequirement.objects.create(
                    job_card=self,
                    category=template.category,
                    name=template.name,
                    description=template.description,
                    is_mandatory=template.is_mandatory,
                    is_blocking=template.is_blocking,
                    validation_rules=template.validation_rules,
                    display_order=template.display_order,
                    status='NOT_STARTED',
                    source_template=template
                )
                created_count += 1

    return created_count

def get_requirements_summary(self):
    """
    Get summary of requirements status.
    Returns dict with counts and blocking status.
    """
    from floor_app.operations.planning.models import JobRequirement

    reqs = self.requirements.all()

    return {
        'total': reqs.count(),
        'completed': reqs.filter(status='COMPLETED').count(),
        'in_progress': reqs.filter(status='IN_PROGRESS').count(),
        'not_started': reqs.filter(status='NOT_STARTED').count(),
        'blocked': reqs.filter(status='BLOCKED').count(),
        'failed': reqs.filter(status='FAILED').count(),
        'waived': reqs.filter(status='WAIVED').count(),
        'has_blocking_incomplete': reqs.filter(
            is_blocking=True
        ).exclude(
            status__in=['COMPLETED', 'WAIVED']
        ).exists(),
        'blocking_requirements': list(
            reqs.filter(is_blocking=True).exclude(
                status__in=['COMPLETED', 'WAIVED']
            ).values('name', 'status', 'description')
        )
    }

def can_proceed_to_production(self):
    """
    Check if all blocking requirements are satisfied.
    Returns (can_proceed: bool, reason: str)
    """
    summary = self.get_requirements_summary()

    if summary['has_blocking_incomplete']:
        blocking = summary['blocking_requirements']
        reason = f"Blocking requirements incomplete: {', '.join([r['name'] for r in blocking])}"
        return False, reason

    return True, "All blocking requirements satisfied"
```

---

## Usage Examples

### Example 1: Check Requirements Before Starting Job

```python
job_card = JobCard.objects.get(job_card_number='2025-ARDT-LV3-042')

# Check if can proceed
can_proceed, reason = job_card.can_proceed_to_production()

if not can_proceed:
    print(f"Cannot start job: {reason}")
    # Display requirements to user
    summary = job_card.get_requirements_summary()
    print(f"Blocking requirements: {summary['blocking_requirements']}")
else:
    print("All requirements satisfied - job can proceed")
```

### Example 2: Update Requirement Status

```python
from floor_app.operations.planning.models import JobRequirement

# Mark requirement as in progress
req = JobRequirement.objects.get(
    job_card__job_card_number='2025-ARDT-LV3-042',
    name='Customer Repair Authorization'
)

req.mark_in_progress(
    user=request.user,
    notes='Sent quotation to customer, awaiting response'
)

# Complete requirement
req.mark_completed(
    user=request.user,
    completion_notes='Customer approved quotation Q-202501-2025-ARDT-LV3-042-R1',
    verification_data={
        'quotation_number': 'Q-202501-2025-ARDT-LV3-042-R1',
        'approved_by': 'John Smith (ENO)',
        'approved_date': '2025-01-15',
        'approval_amount': 12500.00
    }
)
```

### Example 3: Handle Dependency Chain

```python
# Create requirements with dependencies
data_req = JobRequirement.objects.create(
    job_card=job_card,
    category=RequirementCategory.objects.get(code='DATA'),
    name='Serial Number Validation',
    is_blocking=True,
    status='NOT_STARTED'
)

document_req = JobRequirement.objects.create(
    job_card=job_card,
    category=RequirementCategory.objects.get(code='DOCUMENT'),
    name='Bit Design Drawing Review',
    is_blocking=True,
    status='NOT_STARTED'
)

# Document review depends on serial number being validated
document_req.depends_on.add(data_req)

# Try to start document review before dependency
can_start = document_req.can_start()  # Returns False
print(document_req.get_blocking_reason())  # "Waiting on: Serial Number Validation"

# Complete dependency
data_req.mark_completed(user=user)

# Now can start
can_start = document_req.can_start()  # Returns True
document_req.mark_in_progress(user=user)
```

### Example 4: Waive Non-Critical Requirement

```python
req = JobRequirement.objects.get(
    job_card=job_card,
    name='ENO Quality Inspection'
)

# Waive with approval
req.waive(
    user=supervisor,
    waiver_reason='Customer requested expedited delivery, waiving additional inspection',
    waiver_approved_by=manager
)
```

### Example 5: Get Relevant Instructions for Job

```python
from floor_app.operations.planning.models import TechnicalInstruction

job_card = JobCard.objects.get(job_card_number='2025-ARDT-LV3-042')

# Get all relevant instructions
instructions = TechnicalInstruction.get_instructions_for_job_card(job_card)

# Display in UI
for instr in instructions:
    print(f"[{instr.instruction_code}] {instr.title}")
    print(f"  Priority: {instr.get_applies_to_display()}")
    print(f"  {instr.instruction_text[:100]}...")
```

---

## Front-End Integration

### Requirements Dashboard Widget

```python
# In job_card_detail view
def job_card_detail(request, job_card_id):
    job_card = get_object_or_404(JobCard, id=job_card_id)

    # Get requirements grouped by category
    requirements = job_card.requirements.select_related(
        'category', 'assigned_to', 'completed_by'
    ).prefetch_related('depends_on').order_by('category__display_order', 'display_order')

    # Group by category
    requirements_by_category = {}
    for req in requirements:
        cat_code = req.category.code
        if cat_code not in requirements_by_category:
            requirements_by_category[cat_code] = {
                'category': req.category,
                'requirements': []
            }
        requirements_by_category[cat_code]['requirements'].append(req)

    # Get summary
    summary = job_card.get_requirements_summary()

    # Get relevant instructions
    instructions = TechnicalInstruction.get_instructions_for_job_card(job_card)

    context = {
        'job_card': job_card,
        'requirements_by_category': requirements_by_category,
        'requirements_summary': summary,
        'instructions': instructions,
    }

    return render(request, 'production/job_card_detail.html', context)
```

### Template Example

```html
<!-- Requirements Section -->
<div class="requirements-section">
    <h3>Job Requirements</h3>

    <!-- Summary -->
    <div class="requirements-summary">
        <span class="badge badge-success">{{ requirements_summary.completed }} Completed</span>
        <span class="badge badge-info">{{ requirements_summary.in_progress }} In Progress</span>
        <span class="badge badge-secondary">{{ requirements_summary.not_started }} Not Started</span>
        {% if requirements_summary.has_blocking_incomplete %}
            <span class="badge badge-danger">BLOCKED</span>
        {% endif %}
    </div>

    <!-- Requirements by Category -->
    {% for cat_code, data in requirements_by_category.items %}
    <div class="requirement-category">
        <h4>
            <i class="{{ data.category.icon }}" style="color: {{ data.category.color_hex }}"></i>
            {{ data.category.name }}
        </h4>

        <table class="table">
            <thead>
                <tr>
                    <th>Requirement</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for req in data.requirements %}
                <tr class="{% if req.is_blocking and req.status != 'COMPLETED' %}table-warning{% endif %}">
                    <td>
                        {{ req.name }}
                        {% if req.is_blocking %}<span class="badge badge-warning">BLOCKING</span>{% endif %}
                        {% if req.is_mandatory %}<span class="badge badge-danger">REQUIRED</span>{% endif %}
                        <br><small>{{ req.description }}</small>
                    </td>
                    <td>
                        <span class="badge badge-{{ req.get_status_badge_class }}">
                            {{ req.get_status_display }}
                        </span>
                    </td>
                    <td>{{ req.assigned_to|default:"Unassigned" }}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="updateRequirement({{ req.id }})">
                            Update
                        </button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endfor %}

    <!-- Technical Instructions -->
    {% if instructions %}
    <div class="technical-instructions">
        <h3>Relevant Instructions</h3>
        {% for instr in instructions %}
        <div class="instruction-card">
            <h5>[{{ instr.instruction_code }}] {{ instr.title }}</h5>
            <p>{{ instr.description }}</p>
            <div class="instruction-content">
                {{ instr.instruction_text|safe }}
            </div>
            {% if instr.attachments %}
            <div class="attachments">
                <strong>Attachments:</strong>
                {% for file_name, file_url in instr.attachments.items %}
                    <a href="{{ file_url }}" target="_blank">{{ file_name }}</a>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
</div>
```

---

## API Endpoints (Optional REST API)

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class JobRequirementViewSet(viewsets.ModelViewSet):
    queryset = JobRequirement.objects.all()
    serializer_class = JobRequirementSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark requirement as in progress"""
        requirement = self.get_object()

        if not requirement.can_start():
            return Response(
                {'error': requirement.get_blocking_reason()},
                status=status.HTTP_400_BAD_REQUEST
            )

        requirement.mark_in_progress(
            user=request.user,
            notes=request.data.get('notes', '')
        )

        return Response(self.get_serializer(requirement).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark requirement as completed"""
        requirement = self.get_object()

        requirement.mark_completed(
            user=request.user,
            completion_notes=request.data.get('notes', ''),
            verification_data=request.data.get('verification_data')
        )

        return Response(self.get_serializer(requirement).data)

    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        """Waive requirement"""
        requirement = self.get_object()

        if requirement.is_mandatory and not request.data.get('waiver_approved_by'):
            return Response(
                {'error': 'Mandatory requirements require approval to waive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        requirement.waive(
            user=request.user,
            waiver_reason=request.data.get('reason', ''),
            waiver_approved_by=request.data.get('approved_by')
        )

        return Response(self.get_serializer(requirement).data)
```

---

## Admin Integration

```python
from django.contrib import admin
from floor_app.operations.planning.models import (
    RequirementCategory,
    RequirementTemplate,
    JobRequirement,
    TechnicalInstruction,
)

@admin.register(RequirementCategory)
class RequirementCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'display_order', 'icon', 'color_hex']
    list_editable = ['display_order']
    ordering = ['display_order']

@admin.register(RequirementTemplate)
class RequirementTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'is_mandatory', 'is_blocking',
        'is_active', 'display_order'
    ]
    list_filter = ['category', 'is_mandatory', 'is_blocking', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['applies_to_job_types']

@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = [
        'job_card', 'name', 'category', 'status',
        'is_mandatory', 'is_blocking', 'assigned_to'
    ]
    list_filter = ['status', 'category', 'is_mandatory', 'is_blocking']
    search_fields = ['job_card__job_card_number', 'name']
    readonly_fields = [
        'started_at', 'started_by', 'completed_at', 'completed_by',
        'failed_at', 'waived_at', 'waived_by'
    ]
    filter_horizontal = ['depends_on']

@admin.register(TechnicalInstruction)
class TechnicalInstructionAdmin(admin.ModelAdmin):
    list_display = [
        'instruction_code', 'title', 'applies_to',
        'is_active', 'display_order'
    ]
    list_filter = ['applies_to', 'is_active', 'job_type']
    search_fields = ['instruction_code', 'title', 'description']
    ordering = ['display_order']
```

---

## Testing

### Unit Test Example

```python
from django.test import TestCase
from floor_app.operations.production.models import JobCard
from floor_app.operations.planning.models import (
    RequirementCategory,
    RequirementTemplate,
    JobRequirement,
)

class RequirementSystemTestCase(TestCase):

    def setUp(self):
        self.category = RequirementCategory.objects.create(
            code='DATA',
            name='Required Data'
        )

        self.template = RequirementTemplate.objects.create(
            category=self.category,
            name='Serial Number',
            applies_to_job_types=['REPAIR'],
            is_blocking=True
        )

    def test_auto_population(self):
        """Test that requirements auto-populate on job card creation"""
        job_card = JobCard.objects.create(
            job_type='REPAIR',
            # ... other fields
        )

        job_card.populate_requirements()

        self.assertEqual(job_card.requirements.count(), 1)
        req = job_card.requirements.first()
        self.assertEqual(req.name, 'Serial Number')
        self.assertTrue(req.is_blocking)

    def test_blocking_check(self):
        """Test that blocking requirements prevent job start"""
        job_card = JobCard.objects.create(job_type='REPAIR')
        job_card.populate_requirements()

        can_proceed, reason = job_card.can_proceed_to_production()
        self.assertFalse(can_proceed)

        # Complete requirement
        req = job_card.requirements.first()
        req.mark_completed(user=None)

        can_proceed, reason = job_card.can_proceed_to_production()
        self.assertTrue(can_proceed)
```

---

## Next Steps

1. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Populate Initial Data**
   - Create requirement categories
   - Create standard templates
   - Create technical instructions

3. **Add Signal/Hook**
   - Add auto-population signal to JobCard creation
   - Or add manual call in JobCard view

4. **Build UI**
   - Requirements dashboard widget
   - Requirement update modal
   - Technical instructions sidebar
   - Blocking indicator on job card list

5. **Testing**
   - Create test cases
   - Test dependency chains
   - Test blocking logic
   - Test template applicability

---

## Summary

The Requirements System provides:

✅ **Structured Tracking** - Categorized requirements with clear status
✅ **Auto-Population** - Templates automatically apply based on job attributes
✅ **Dependency Management** - Requirements can depend on other requirements
✅ **Blocking Logic** - Critical requirements can block job progression
✅ **Technical Instructions** - Context-aware procedures displayed to operators
✅ **Audit Trail** - Full history of who did what and when
✅ **Flexibility** - Waiver system for exceptions with approval
✅ **Validation** - JSON rules for automated checking

This system ensures that all necessary prerequisites are in place before work begins, reducing errors and rework.

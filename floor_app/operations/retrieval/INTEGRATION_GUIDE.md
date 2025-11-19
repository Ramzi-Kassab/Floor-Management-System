# Retrieval System Integration Guide

This guide walks through integrating the Retrieval/Undo system into existing Floor Management System modules.

## Quick Start Integration

### Step 1: Update Your Model

Add `RetrievableMixin` to any model that needs retrieval capability:

```python
# Example: floor_app/operations/hoc/models/__init__.py
from floor_app.operations.retrieval.mixins import RetrievableMixin
from floor_app.mixins import AuditMixin

class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    """
    Note: RetrievableMixin must come BEFORE AuditMixin in the inheritance chain.
    This ensures the mixin methods are available.
    """
    # Your existing fields
    employee = models.ForeignKey(User, ...)
    equipment = models.ForeignKey(Equipment, ...)
    # ... etc
```

### Step 2: Add Button to Detail Template

Update your detail template to include the retrieval button:

```html
<!-- Example: floor_app/operations/hoc/templates/hoc/detail.html -->
{% load retrieval_tags %}

<div class="card-header">
    <h5>{{ hoc }}</h5>
    <div class="btn-group">
        <!-- Existing buttons -->
        <a href="{% url 'hoc:edit' hoc.pk %}" class="btn btn-primary btn-sm">Edit</a>

        <!-- Add retrieval button -->
        {% retrieval_button hoc request.user %}
    </div>
</div>
```

### Step 3: Add Retrieval Status to List Views

Show retrieval status in list views:

```html
<!-- Example: floor_app/operations/hoc/templates/hoc/list.html -->
{% load retrieval_tags %}

<table class="table">
    <thead>
        <tr>
            <th>ID</th>
            <th>Employee</th>
            <th>Status</th>
            <th>Retrieval Status</th>
        </tr>
    </thead>
    <tbody>
        {% for hoc in hocs %}
        <tr>
            <td>{{ hoc.id }}</td>
            <td>{{ hoc.employee }}</td>
            <td>{{ hoc.status }}</td>
            <td>
                {% if hoc.has_retrieval_requests %}
                    {% with hoc.get_pending_retrieval_request as pending %}
                        {% if pending %}
                            <span class="badge bg-warning">
                                <i class="bi bi-clock"></i> Pending Retrieval
                            </span>
                        {% endif %}
                    {% endwith %}
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Step 4: Add Dashboard Links

Add links to retrieval dashboards in your navigation:

```html
<!-- Example: templates/base.html or navigation template -->
<li class="nav-item">
    <a class="nav-link" href="{% url 'retrieval:dashboard' %}">
        <i class="bi bi-arrow-counterclockwise"></i> My Retrievals
        {% load retrieval_tags %}
        {% employee_accuracy request.user 'month' as accuracy %}
        {% if accuracy.retrieval_requests > 0 %}
            <span class="badge bg-warning">{{ accuracy.retrieval_requests }}</span>
        {% endif %}
    </a>
</li>

<!-- For supervisors -->
{% if request.user.is_staff or request.user.groups.filter(name='Supervisors').exists %}
<li class="nav-item">
    <a class="nav-link" href="{% url 'retrieval:supervisor_dashboard' %}">
        <i class="bi bi-person-check"></i> Approve Retrievals
        {% supervisor_pending_count request.user as pending %}
        {% if pending > 0 %}
            <span class="badge bg-danger">{{ pending }}</span>
        {% endif %}
    </a>
</li>
{% endif %}
```

## Advanced Integration

### Custom Time Windows

Set different time windows for different models:

```python
# For HOC - strict 10-minute window
class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    RETRIEVAL_TIME_WINDOW_MINUTES = 10
    # ...

# For FIVES Audits - more lenient 30-minute window
class FivesAudit(RetrievableMixin, AuditMixin, models.Model):
    RETRIEVAL_TIME_WINDOW_MINUTES = 30
    # ...
```

### Custom Dependency Checks

Add custom business logic for dependency checking:

```python
class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    # ...

    def _check_dependencies(self):
        """Override to add custom dependency checks."""
        # Get standard dependencies
        dependencies = super()._check_dependencies()

        # Add custom check: prevent retrieval if already approved
        if self.status == 'APPROVED':
            dependencies.append({
                'model': 'ApprovalWorkflow',
                'count': 1,
                'description': 'HOC is already approved - cannot retrieve',
                'model_verbose': 'Approval Status'
            })

        # Add custom check: prevent if equipment already returned
        if hasattr(self, 'equipment_returned') and self.equipment_returned:
            dependencies.append({
                'model': 'EquipmentReturn',
                'count': 1,
                'description': 'Equipment already returned',
                'model_verbose': 'Equipment Status'
            })

        return dependencies
```

### Custom Supervisor Lookup

Override supervisor lookup for your organizational structure:

```python
class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    # ...

    def _get_supervisor(self, employee):
        """Custom supervisor lookup for HOC."""
        # Try employee's direct supervisor
        if hasattr(employee, 'employee_profile'):
            profile = employee.employee_profile
            if profile.supervisor:
                return profile.supervisor

        # Fallback to department manager
        if hasattr(employee, 'department'):
            dept = employee.department
            if dept.manager:
                return dept.manager

        # Fallback to HR manager for specific group
        if employee.groups.filter(name='Equipment Handlers').exists():
            equipment_manager = User.objects.filter(
                groups__name='Equipment Managers'
            ).first()
            if equipment_manager:
                return equipment_manager

        # Final fallback to superuser
        return super()._get_supervisor(employee)
```

### Custom Retrieval Actions

Override `perform_retrieval` for custom business logic:

```python
class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    # ...

    def perform_retrieval(self, retrieval_request):
        """Custom retrieval logic for HOC."""
        if retrieval_request.action_type == 'DELETE':
            # Custom logic before deletion
            # Return equipment to inventory
            if hasattr(self, 'equipment'):
                self.equipment.status = 'AVAILABLE'
                self.equipment.save()

            # Notify stakeholders
            self._notify_retrieval_stakeholders(retrieval_request)

        # Call parent to complete standard retrieval
        super().perform_retrieval(retrieval_request)

        # Custom logic after retrieval
        # Create audit log entry
        self._create_retrieval_audit_log(retrieval_request)
```

## Integration with Existing Systems

### FIVES Audit System

```python
# floor_app/operations/fives/models.py
from floor_app.operations.retrieval.mixins import RetrievableMixin

class FivesAudit(RetrievableMixin, AuditMixin, models.Model):
    # Set strict time window for audits
    RETRIEVAL_TIME_WINDOW_MINUTES = 10

    # Custom dependency check for audit findings
    def _check_dependencies(self):
        dependencies = super()._check_dependencies()

        # Check for linked action items
        if self.action_items.exists():
            dependencies.append({
                'model': 'ActionItem',
                'count': self.action_items.count(),
                'description': f'{self.action_items.count()} action items created from this audit'
            })

        return dependencies
```

### Approval Workflow Integration

```python
# floor_app/operations/approvals/models.py
from floor_app.operations.retrieval.mixins import RetrievableMixin

class ApprovalRequest(RetrievableMixin, models.Model):
    # Prevent retrieval if already approved
    def can_be_retrieved(self):
        can_retrieve, reasons = super().can_be_retrieved()

        if self.status == 'APPROVED':
            can_retrieve = False
            reasons.append("Cannot retrieve approved requests")

        return can_retrieve, reasons
```

### GPS Verification System

```python
# floor_app/operations/gps_system/models.py
from floor_app.operations.retrieval.mixins import RetrievableMixin

class GPSVerification(RetrievableMixin, AuditMixin, models.Model):
    # Very short window for GPS verifications
    RETRIEVAL_TIME_WINDOW_MINUTES = 5

    # Custom check for location-based restrictions
    def can_be_retrieved(self):
        can_retrieve, reasons = super().can_be_retrieved()

        # Check if user is still at the same location
        if self.location != self.employee.current_location:
            can_retrieve = False
            reasons.append("Employee has moved from verification location")

        return can_retrieve, reasons
```

## Dashboard Integration

### Add Metrics to Main Dashboard

```html
<!-- templates/dashboard.html -->
{% load retrieval_tags %}

<div class="row">
    <!-- Existing dashboard widgets -->

    <!-- Add retrieval metrics -->
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5>My Accuracy Metrics</h5>
            </div>
            <div class="card-body">
                {% accuracy_badge request.user 'month' 'normal' %}

                <hr>

                <a href="{% url 'retrieval:my_metrics' %}" class="btn btn-outline-primary btn-sm">
                    View Detailed Metrics
                </a>

                {% if pending_requests > 0 %}
                <a href="{% url 'retrieval:dashboard' %}" class="btn btn-warning btn-sm">
                    {{ pending_requests }} Pending Requests
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
```

### Supervisor Dashboard Widget

```html
<!-- For supervisors on main dashboard -->
{% load retrieval_tags %}
{% supervisor_pending_count request.user as pending_count %}

{% if pending_count > 0 %}
<div class="alert alert-warning">
    <h5><i class="bi bi-exclamation-triangle"></i> Action Required</h5>
    <p>
        You have <strong>{{ pending_count }}</strong> pending retrieval request(s)
        waiting for your approval.
    </p>
    <a href="{% url 'retrieval:supervisor_dashboard' %}" class="btn btn-warning">
        Review Requests
    </a>
</div>
{% endif %}
```

## Notifications Integration

### Email Templates

Create custom email templates for your organization:

```html
<!-- templates/retrieval/email/supervisor_notification.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h2>Retrieval Request Requires Your Approval</h2>

    <p>Dear {{ supervisor.get_full_name }},</p>

    <p>
        <strong>{{ request.employee.get_full_name }}</strong> has submitted a retrieval
        request that requires your approval.
    </p>

    <table>
        <tr>
            <th>Request ID:</th>
            <td>#{{ request.id }}</td>
        </tr>
        <tr>
            <th>Object:</th>
            <td>{{ request.get_object_display }}</td>
        </tr>
        <tr>
            <th>Action:</th>
            <td>{{ request.get_action_type_display }}</td>
        </tr>
        <tr>
            <th>Reason:</th>
            <td>{{ request.reason }}</td>
        </tr>
        <tr>
            <th>Time Elapsed:</th>
            <td>{{ request.time_elapsed }}</td>
        </tr>
    </table>

    <p>
        <a href="{{ approval_url }}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Review Request
        </a>
    </p>

    <p>Thank you,<br>Floor Management System</p>
</body>
</html>
```

## Testing Integration

### Unit Tests

```python
# floor_app/operations/hoc/tests.py
from django.test import TestCase
from floor_app.operations.retrieval.models import RetrievalRequest
from floor_app.operations.hoc.models import HandOverCertificate

class HOCRetrievalTestCase(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user('employee', 'test@test.com', 'pass')
        self.supervisor = User.objects.create_user('supervisor', 'super@test.com', 'pass')
        self.hoc = HandOverCertificate.objects.create(
            employee=self.employee,
            equipment=self.equipment
        )

    def test_can_create_retrieval_request(self):
        """Test that HOC can create retrieval request."""
        request = self.hoc.create_retrieval_request(
            employee=self.employee,
            reason="Made a mistake",
            action_type='DELETE'
        )

        self.assertIsNotNone(request)
        self.assertEqual(request.employee, self.employee)
        self.assertEqual(request.status, 'AUTO_APPROVED')  # Within time window

    def test_dependencies_prevent_retrieval(self):
        """Test that dependencies block retrieval."""
        # Create dependent record
        EquipmentReturn.objects.create(hoc=self.hoc)

        can_retrieve, reasons = self.hoc.can_be_retrieved()

        self.assertFalse(can_retrieve)
        self.assertIn('dependent', ' '.join(reasons).lower())
```

## Migration Checklist

- [ ] Add `RetrievableMixin` to target models
- [ ] Update detail templates with retrieval buttons
- [ ] Add retrieval status to list views
- [ ] Update navigation with retrieval links
- [ ] Test retrieval workflow end-to-end
- [ ] Configure supervisor assignments
- [ ] Set up email notifications
- [ ] Train users on the system
- [ ] Monitor metrics for the first week

## Support

For questions or issues with integration, refer to:
- README.md - Complete system documentation
- Example implementations in existing modules
- Development team contact

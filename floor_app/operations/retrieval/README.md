# Retrieval/Undo System

A comprehensive system for allowing employees to undo mistakes within a time window with supervisor approval and full audit trails.

## Features

- ✅ **Auto-approval within 15-minute time window** - Mistakes caught quickly are automatically approved
- ✅ **Supervisor notifications** - Automatic email and in-app notifications for manual approvals
- ✅ **Dependency checking** - Prevents retrieval if dependent processes exist
- ✅ **Full audit trail** - Snapshots original data for complete tracking
- ✅ **Employee accuracy metrics** - Track performance over time
- ✅ **Generic retrieval capability** - Works with any model via mixin

## Installation

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'floor_app.operations.retrieval',
]
```

### 2. Include URLs

```python
# floor_app/urls.py or your main urls.py
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('operations/retrieval/', include('floor_app.operations.retrieval.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py makemigrations retrieval
python manage.py migrate
```

## Usage

### Adding Retrieval Capability to a Model

```python
# models.py
from django.db import models
from floor_app.mixins import AuditMixin
from floor_app.operations.retrieval.mixins import RetrievableMixin

class MyModel(RetrievableMixin, AuditMixin, models.Model):
    """
    Any model that needs retrieval capability.

    Note: RetrievableMixin should come first in inheritance order.
    """
    name = models.CharField(max_length=100)
    # ... other fields
```

### Creating a Retrieval Request

```python
# In your view or code
obj = MyModel.objects.get(pk=1)

# Check if can be retrieved
can_retrieve, reasons = obj.can_be_retrieved()

if can_retrieve:
    # Create retrieval request
    request = obj.create_retrieval_request(
        employee=request.user,
        reason="Made a mistake in data entry - entered wrong quantity",
        action_type='DELETE'  # or 'EDIT', 'UNDO', 'RESTORE'
    )

    # Auto-approval happens automatically if within time window
    if request.status == 'AUTO_APPROVED':
        print("Request auto-approved!")
    else:
        print("Request sent to supervisor for approval")
```

### Adding "Request Retrieval" Button to Templates

```html
<!-- In your detail template -->
{% if object.can_be_retrieved %}
<a href="{% url 'retrieval:create_request' object|content_type_id object.pk %}"
   class="btn btn-warning">
    <i class="bi bi-arrow-counterclockwise"></i> Request Retrieval
</a>
{% endif %}
```

### Completing an Approved Retrieval

```python
# After supervisor approval
retrieval_request = RetrievalRequest.objects.get(pk=request_id)

if retrieval_request.is_approved:
    obj = retrieval_request.content_object
    obj.perform_retrieval(retrieval_request)
    # Retrieval is now completed
```

## URL Patterns

| URL | View | Description |
|-----|------|-------------|
| `/operations/retrieval/` | `retrieval_dashboard` | Employee's retrieval requests dashboard |
| `/operations/retrieval/create/<ct_id>/<obj_id>/` | `create_retrieval_request` | Create new retrieval request |
| `/operations/retrieval/request/<pk>/` | `request_detail` | View request details |
| `/operations/retrieval/request/<pk>/complete/` | `complete_retrieval` | Execute approved retrieval |
| `/operations/retrieval/request/<pk>/cancel/` | `cancel_retrieval` | Cancel pending request |
| `/operations/retrieval/supervisor/` | `supervisor_dashboard` | Supervisor approval dashboard |
| `/operations/retrieval/supervisor/<pk>/` | `approve_retrieval` | Approve/reject request |
| `/operations/retrieval/metrics/` | `employee_metrics` | View accuracy metrics |

## Models

### RetrievalRequest

Main model tracking retrieval requests.

**Key Fields:**
- `employee` - User requesting retrieval
- `supervisor` - Supervisor who approves
- `content_type/object_id` - Generic FK to any model
- `action_type` - DELETE, EDIT, UNDO, or RESTORE
- `reason` - Text reason for retrieval
- `status` - PENDING, AUTO_APPROVED, APPROVED, REJECTED, COMPLETED
- `original_data` - JSON snapshot of original object
- `has_dependent_processes` - Whether dependencies exist
- `time_elapsed` - Time from creation to request

**Key Methods:**
- `is_within_time_window(minutes=15)` - Check if within auto-approval window
- `can_auto_approve()` - Check if eligible for auto-approval
- `approve(approved_by, auto=False)` - Approve the request
- `reject(rejected_by, reason)` - Reject the request
- `complete()` - Mark as completed

### RetrievalMetric

Aggregated metrics for employee accuracy.

**Key Fields:**
- `employee` - Employee being measured
- `period_type` - DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
- `period_start/period_end` - Date range
- `total_actions` - Total actions in period
- `retrieval_requests` - Number of retrieval requests
- `accuracy_rate` - Calculated accuracy percentage

## Mixin Methods

### RetrievableMixin

Add to any model to enable retrieval capability.

**Methods:**
- `can_be_retrieved()` - Returns (bool, list_of_reasons)
- `create_retrieval_request(employee, reason, action_type='UNDO')` - Create request
- `perform_retrieval(retrieval_request)` - Execute retrieval
- `get_retrieval_requests()` - Get all retrieval requests for object
- `has_retrieval_requests()` - Check if any requests exist

**Class Attributes to Override:**
- `RETRIEVAL_TIME_WINDOW_MINUTES` - Default: 15 minutes

## Services

### RetrievalService

Business logic for retrieval operations.

**Static Methods:**
- `check_dependencies(obj)` - Check for dependent processes
- `notify_supervisor(retrieval_request)` - Send notifications
- `notify_employee_decision(retrieval_request)` - Notify employee of decision
- `calculate_employee_accuracy(employee, period='month')` - Calculate metrics
- `calculate_and_save_metrics(employee, period_type='MONTHLY')` - Save metrics
- `get_supervisor_pending_count(supervisor)` - Count pending approvals
- `auto_approve_eligible_requests()` - Batch auto-approve eligible requests

## Configuration

### Time Window

Change auto-approval time window globally:

```python
# In your model
class MyModel(RetrievableMixin, models.Model):
    RETRIEVAL_TIME_WINDOW_MINUTES = 30  # Override to 30 minutes
    # ...
```

### Supervisor Lookup

Override supervisor lookup logic:

```python
# In your RetrievableMixin subclass
def _get_supervisor(self, employee):
    """Custom supervisor lookup logic."""
    # Your custom logic here
    return supervisor_user
```

## Permissions

- **Employees** can:
  - Create retrieval requests
  - View their own requests
  - Complete approved requests
  - Cancel pending requests

- **Supervisors** can:
  - View pending requests
  - Approve/reject requests
  - View employee metrics

- **Staff/Admins** can:
  - View all requests
  - Override decisions
  - Access admin interface

## Integration Examples

### Example 1: HOC (Hand Over Certificate)

```python
# floor_app/operations/hoc/models/__init__.py
from floor_app.operations.retrieval.mixins import RetrievableMixin

class HandOverCertificate(RetrievableMixin, AuditMixin, models.Model):
    # ... existing fields
    pass
```

Add button to template:
```html
<!-- In HOC detail template -->
{% if hoc.can_be_retrieved %}
<a href="{% url 'retrieval:create_request' hoc|content_type_id hoc.pk %}"
   class="btn btn-warning btn-sm">
    <i class="bi bi-arrow-counterclockwise"></i> Request Undo
</a>
{% endif %}
```

### Example 2: FIVES Audit

```python
# floor_app/operations/fives/models.py
class FivesAudit(RetrievableMixin, AuditMixin, models.Model):
    # Set custom time window
    RETRIEVAL_TIME_WINDOW_MINUTES = 10  # 10 minutes for audits
    # ... fields
```

### Example 3: Approval Records

```python
# Any approval model
class ApprovalRecord(RetrievableMixin, models.Model):
    # Override to check custom dependencies
    def _check_dependencies(self):
        dependencies = super()._check_dependencies()

        # Add custom dependency checks
        if self.has_downstream_approvals():
            dependencies.append({
                'model': 'DownstreamApproval',
                'count': self.downstream_count,
                'description': 'Has downstream approvals'
            })

        return dependencies
```

## Scheduled Tasks (Optional)

### Auto-Approve Eligible Requests

Set up a periodic task (using Celery, cron, etc.):

```python
# tasks.py
from floor_app.operations.retrieval.services import RetrievalService

def auto_approve_retrievals():
    """Run every 5 minutes to auto-approve eligible requests."""
    count = RetrievalService.auto_approve_eligible_requests()
    print(f"Auto-approved {count} retrieval requests")
```

### Calculate Metrics

```python
# tasks.py
from django.contrib.auth import get_user_model
from floor_app.operations.retrieval.services import RetrievalService

def calculate_daily_metrics():
    """Run daily to calculate metrics."""
    User = get_user_model()
    for user in User.objects.filter(is_active=True):
        RetrievalService.calculate_and_save_metrics(user, 'DAILY')
```

## Email Templates (Optional)

Create custom email templates:

```
templates/
└── retrieval/
    └── email/
        ├── supervisor_notification.html
        ├── supervisor_notification.txt
        ├── employee_approved.html
        └── employee_rejected.html
```

## Metrics Dashboard Integration

Add to main dashboard:

```html
<!-- In main dashboard -->
<div class="card">
    <div class="card-header">
        <h5>My Accuracy This Month</h5>
    </div>
    <div class="card-body">
        {% load retrieval_tags %}
        {% employee_accuracy request.user 'month' as accuracy %}
        <h2>{{ accuracy.accuracy_rate }}%</h2>
        <p>{{ accuracy.total_actions }} actions, {{ accuracy.retrieval_requests }} retrievals</p>
    </div>
</div>
```

## API Integration (Future)

The system is designed to support REST API integration:

```python
# api/serializers.py (example)
from rest_framework import serializers
from floor_app.operations.retrieval.models import RetrievalRequest

class RetrievalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetrievalRequest
        fields = '__all__'
```

## Troubleshooting

### Issue: Supervisor not found

Solution: Implement custom `_get_supervisor` method in your model.

### Issue: Dependencies not detected

Solution: Ensure related_name is set on ForeignKey fields pointing to your model.

### Issue: Auto-approval not working

Solution: Check that `created_at` field exists on your model (provided by AuditMixin).

## Support

For issues or questions, contact the development team or refer to the system documentation.

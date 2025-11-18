# Workflow Automation Documentation

**Last Updated:** November 18, 2025

## Overview

Comprehensive workflow automation including approval processes, state machines, business rules, and task scheduling.

## Features

### 1. Workflow State Machine
- Define custom workflow states
- Allowed transitions between states
- Permission-based transitions
- Automatic state transitions based on conditions
- Workflow history tracking

### 2. Approval Workflows
- Multi-level approvals
- Parallel or sequential approval chains
- Automatic approver notifications
- Approval comments and history
- Rejection handling

### 3. Business Rules Engine
- Condition-based rule execution
- Multiple actions per rule
- Rule prioritization
- Dynamic rule management

### 4. Task Scheduling
- One-time tasks
- Recurring tasks (interval, daily, weekly, cron)
- Task retry logic
- Execution history
- Task status monitoring

## Usage Examples

### Workflow State Machine

```python
from core.workflows import WorkflowEngine, WorkflowState

# Define states
states = [
    WorkflowState('draft', 'Draft', is_initial=True,
                 allowed_transitions=['submitted']),
    WorkflowState('submitted', 'Submitted',
                 allowed_transitions=['approved', 'rejected']),
    WorkflowState('approved', 'Approved', is_final=True),
    WorkflowState('rejected', 'Rejected', is_final=True),
]

# Create engine
engine = WorkflowEngine(states)

# Transition object
engine.transition(my_object, 'submitted', user=request.user,
                 comment='Ready for review')
```

### Approval Workflow

```python
from core.workflows import ApprovalWorkflow

# Define approval levels
levels = [
    {
        'name': 'Manager Approval',
        'approvers': [manager1, manager2],
        'required': 1  # At least 1 approval needed
    },
    {
        'name': 'Director Approval',
        'approvers': [director],
        'required': 1
    }
]

# Create workflow
workflow = ApprovalWorkflow(approval_levels=levels)

# Submit for approval
workflow.submit_for_approval(my_object, submitted_by=user,
                              comment='Please review')

# Approve
workflow.approve(my_object, user=manager1,
                comment='Looks good')

# Reject
workflow.reject(my_object, user=manager1,
               reason='Missing information')
```

### Business Rules

```python
from core.workflows import BusinessRule, BusinessRulesEngine

# Define rule
def condition(context):
    return context['amount'] > 10000

def action(context):
    # Send notification to manager
    notify_manager(context['object'])

rule = BusinessRule(
    name='high_value_approval',
    condition=condition,
    actions=[action],
    priority=10
)

# Create engine and add rule
engine = BusinessRulesEngine()
engine.add_rule(rule)

# Execute rules
context = {'amount': 15000, 'object': my_object}
results = engine.execute_all(context)
```

### Task Scheduling

```python
from core.tasks import ScheduledTask, scheduler, scheduled_task

# Method 1: Create task directly
def my_task():
    print("Task executed!")

task = ScheduledTask(
    name='daily_cleanup',
    func=my_task,
    schedule_type='daily',
    schedule_data={'hour': 2, 'minute': 0}
)

scheduler.register_task(task)

# Method 2: Use decorator
@scheduled_task(schedule_type='interval', interval=3600)
def hourly_task():
    print("Running every hour")

# Run pending tasks (call from management command or cron)
scheduler.run_pending()

# Get task status
status = scheduler.get_status()
```

## Pre-defined Scheduled Tasks

### Daily Tasks
- `cleanup_old_notifications` - Runs at 2:00 AM
  - Removes notifications older than 90 days

- `cleanup_old_activities` - Runs at 3:00 AM
  - Removes activity logs older than 365 days

### Weekly Tasks
- `generate_weekly_reports` - Runs Monday at 1:00 AM
  - Generates weekly system reports

### Interval Tasks
- `check_system_health` - Runs every 5 minutes
  - Monitors system health

## Management Command

Run scheduled tasks:

```bash
# Run pending tasks
python manage.py run_scheduled_tasks

# Run specific task
python manage.py run_scheduled_tasks --task=cleanup_old_notifications

# Show task status
python manage.py run_scheduled_tasks --status
```

## Integration Example

```python
# In your model
class PurchaseOrder(models.Model):
    workflow_state = models.CharField(max_length=50, default='draft')
    approval_data = models.JSONField(null=True, blank=True)

    # ... other fields

# In your view
def submit_po(request, po_id):
    po = get_object_or_404(PurchaseOrder, id=po_id)

    # Submit for approval
    workflow = ApprovalWorkflow(approval_levels=[...])
    workflow.submit_for_approval(po, submitted_by=request.user)

    # Transition state
    engine = WorkflowEngine(states=[...])
    engine.transition(po, 'submitted', user=request.user)

    return redirect('po_detail', po_id=po_id)
```

## Files Created

- `core/workflows.py` (470 lines) - Workflow engine, approvals, business rules
- `core/tasks.py` (370 lines) - Task scheduling system

## Total: ~840 lines of workflow automation code

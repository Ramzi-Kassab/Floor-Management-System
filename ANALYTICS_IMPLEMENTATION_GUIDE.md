# Analytics, KPI Tracking & Rule Engine - Complete Implementation Guide

## Table of Contents

1. [Overview](#overview)
2. [Backend Implementation (COMPLETED)](#backend-implementation)
3. [Installation & Configuration](#installation--configuration)
4. [Frontend Implementation](#frontend-implementation)
5. [Usage Examples](#usage-examples)
6. [Test Data Generation](#test-data-generation)
7. [Business Use Cases](#business-use-cases)

---

## Overview

This system provides three integrated subsystems:

1. **App Usage Analytics** - Track who uses what features, when, and how often
2. **Information Request Tracking** - Measure email reduction and identify missing features
3. **Automation Rule Engine** - Proactive condition monitoring and automated actions

**Business Value:**
- Prove ROI of digital transformation (email reduction %)
- Data-driven feature prioritization (usage analytics)
- Proactive operations (rule alerts before problems escalate)
- Identify unused features (candidates for removal or improvement)

---

## Backend Implementation (COMPLETED ✅)

### Models Created

**Analytics Events:**
- `AppEvent` - All user interactions (page views, reports, actions, exports)
- `EventSummary` - Pre-aggregated statistics (hourly/daily/weekly/monthly)

**Information Requests:**
- `InformationRequest` - Email/phone/WhatsApp requests tracking
- `RequestTrend` - Pre-aggregated request statistics

**Automation Rules:**
- `AutomationRule` - Data-driven rule definitions (JSON DSL)
- `AutomationRuleExecution` - Audit log of rule evaluations
- `RuleTemplate` - Pre-configured rule templates

### Rule Engine Components

**Condition Parser** (`rule_engine/conditions.py`):
- Parses JSON condition definitions safely
- Supports: threshold, age, field_comparison, queryset_count, compound, custom
- No arbitrary code execution

**Rule Evaluator** (`rule_engine/evaluator.py`):
- Coordinates rule execution
- Handles single objects or querysets
- Performance tracking

**Action Executor** (`rule_engine/actions.py`):
- Executes actions when rules trigger
- Supports: LOG_ONLY, CREATE_ALERT, SEND_NOTIFICATION, UPDATE_FIELD, CREATE_TASK, RUN_SCRIPT, WEBHOOK

### Middleware & Decorators

**Middleware:**
- `EventTrackingMiddleware` - Automatic page view tracking

**Decorators:**
- `@track_view` - Manual view tracking
- `@track_report` - Report tracking
- `@track_export` - Export tracking
- `@track_action` - Action tracking
- `@track_search` - Search query tracking
- `@track_function` - System function tracking

---

## Installation & Configuration

### Step 1: Add to INSTALLED_APPS

```python
# settings.py

INSTALLED_APPS = [
    # ... existing apps
    'floor_app.operations.analytics',
]
```

### Step 2: Add Middleware

```python
# settings.py

MIDDLEWARE = [
    # ... existing middleware (keep order)
    'floor_app.operations.analytics.middleware.event_tracker.EventTrackingMiddleware',
]
```

### Step 3: Configure Analytics Settings

```python
# settings.py

# Analytics Configuration
ANALYTICS_TRACKING_ENABLED = True
ANALYTICS_TRACK_ANONYMOUS = False  # Don't track anonymous users
ANALYTICS_EXCLUDED_PATHS = [
    '/admin/',
    '/static/',
    '/media/',
    '/__debug__/',
    '/favicon.ico',
]
ANALYTICS_ASYNC_LOGGING = True  # Use Celery for async logging (recommended)
```

### Step 4: Configure Celery Beat (Scheduled Tasks)

```python
# celeryconfig.py or settings.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Generate hourly event summaries
    'generate-event-summaries': {
        'task': 'floor_app.operations.analytics.tasks.generate_event_summaries',
        'schedule': crontab(minute=0),  # Every hour at :00
    },

    # Run automation rules every 15 minutes
    'run-automation-rules': {
        'task': 'floor_app.operations.analytics.tasks.run_automation_rules',
        'schedule': crontab(minute='*/15'),
    },

    # Generate daily request trends
    'generate-request-trends': {
        'task': 'floor_app.operations.analytics.tasks.generate_request_trends',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },

    # Cleanup old events (weekly)
    'cleanup-old-events': {
        'task': 'floor_app.operations.analytics.tasks.cleanup_old_events',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Monday 2 AM
        'kwargs': {'days': 90},  # Keep 90 days of history
    },
}
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations analytics
python manage.py migrate analytics
```

### Step 6: Create Initial Data

```bash
# Generate test data
python manage.py generate_analytics_test_data

# Create rule templates
python manage.py create_rule_templates

# Create requirement categories (if not done yet)
python manage.py create_analytics_categories
```

---

## Frontend Implementation

### URL Configuration

```python
# floor_app/operations/analytics/urls.py

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main Dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),

    # Usage Analytics
    path('usage/', views.UsageAnalyticsView.as_view(), name='usage'),
    path('usage/events/', views.EventListView.as_view(), name='event_list'),
    path('usage/export/', views.export_usage_report, name='export_usage'),

    # Information Requests
    path('requests/', views.InformationRequestListView.as_view(), name='request_list'),
    path('requests/create/', views.InformationRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', views.InformationRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/edit/', views.InformationRequestUpdateView.as_view(), name='request_update'),
    path('requests/<int:pk>/mark-covered/', views.mark_request_covered, name='mark_covered'),
    path('requests/email-reduction/', views.EmailReductionDashboardView.as_view(), name='email_reduction'),

    # Automation Rules
    path('rules/', views.AutomationRuleListView.as_view(), name='rule_list'),
    path('rules/create/', views.AutomationRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/', views.AutomationRuleDetailView.as_view(), name='rule_detail'),
    path('rules/<int:pk>/edit/', views.AutomationRuleUpdateView.as_view(), name='rule_update'),
    path('rules/<int:pk>/execute/', views.execute_rule_now, name='execute_rule'),
    path('rules/<int:pk>/approve/', views.approve_rule, name='approve_rule'),
    path('rules/<int:pk>/toggle/', views.toggle_rule_active, name='toggle_rule'),
    path('rules/executions/', views.RuleExecutionListView.as_view(), name='execution_list'),
    path('rules/executions/<int:pk>/', views.RuleExecutionDetailView.as_view(), name='execution_detail'),

    # API endpoints (for AJAX)
    path('api/usage-trend/', views.api_usage_trend, name='api_usage_trend'),
    path('api/request-trend/', views.api_request_trend, name='api_request_trend'),
    path('api/rule-stats/', views.api_rule_stats, name='api_rule_stats'),
]
```

### Main Project URLs Integration

```python
# floor_management/urls.py or main urls.py

from django.urls import path, include

urlpatterns = [
    # ... existing patterns
    path('analytics/', include('floor_app.operations.analytics.urls')),
]
```

### Navigation Integration

Add to your base template navigation:

```html
<!-- In templates/base.html or your main nav -->

<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="analyticsDropdown"
       role="button" data-bs-toggle="dropdown">
        <i class="fas fa-chart-line"></i> Analytics & KPIs
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="{% url 'analytics:dashboard' %}">
            <i class="fas fa-tachometer-alt"></i> Main Dashboard
        </a></li>
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="{% url 'analytics:usage' %}">
            <i class="fas fa-users"></i> Usage Analytics
        </a></li>
        <li><a class="dropdown-item" href="{% url 'analytics:email_reduction' %}">
            <i class="fas fa-envelope-open-text"></i> Email Reduction
        </a></li>
        <li><a class="dropdown-item" href="{% url 'analytics:request_list' %}">
            <i class="fas fa-question-circle"></i> Information Requests
        </a></li>
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="{% url 'analytics:rule_list' %}">
            <i class="fas fa-robot"></i> Automation Rules
        </a></li>
        <li><a class="dropdown-item" href="{% url 'analytics:execution_list' %}">
            <i class="fas fa-history"></i> Rule Executions
        </a></li>
    </ul>
</li>
```

---

## Usage Examples

### 1. Tracking Page Views Automatically

The middleware tracks all page views automatically. No code changes needed.

### 2. Manual Event Tracking

```python
from floor_app.operations.analytics.decorators import track_report, track_export

@track_report('Cutter Inventory Report', category='Inventory')
def cutter_inventory_report(request):
    # Your view code
    return render(request, 'inventory/cutter_report.html', context)

@track_export('Job Card Export', format_field='format')
def export_job_cards(request):
    format = request.GET.get('format', 'csv')
    # Your export code
    return response
```

### 3. Logging Information Requests

```python
from floor_app.operations.analytics.models import InformationRequest

# User calls asking about bit status
InformationRequest.objects.create(
    requester_name="John Smith (ENO)",
    requester_email="john@eno.com",
    channel='PHONE',
    request_category='STATUS',
    summary="What's the status of bit SN12345?",
    details="Customer called asking when bit will be ready. No visibility in system.",
    related_serial_unit=serial_unit,
    priority=80,
)
```

### 4. Marking Requests as Covered

```python
# After building "Bit Status Tracker" feature
request = InformationRequest.objects.get(id=123)
request.mark_as_covered(
    view_name='bit_status_tracker',
    url='/production/bits/status/',
    user=request.user
)
```

### 5. Creating Automation Rules

**Simple Stock Alert:**

```python
from floor_app.operations.analytics.models import AutomationRule

AutomationRule.objects.create(
    name="Low Stock Alert - ENO Reclaimed Cutters",
    rule_code="INV_LOW_STOCK_ENO_RECLAIM",
    description="Alert when ENO reclaimed cutter stock drops below 10",
    rule_scope='INVENTORY',
    target_model='inventory.CutterDetail',
    condition_definition={
        "type": "compound",
        "operator": "AND",
        "conditions": [
            {
                "type": "threshold",
                "field": "quantity_on_hand",
                "operator": "<",
                "value": 10
            },
            {
                "type": "field_comparison",
                "field1": "category",
                "operator": "==",
                "field2": "'ENO_RECLAIMED'"
            }
        ]
    },
    action_type='SEND_NOTIFICATION',
    action_config={
        "recipients": ["inventory@company.com"],
        "subject": "Low Stock Alert: {rule_name}",
        "message": "ENO reclaimed cutter stock is low. Current: {context.current_stock}"
    },
    severity='WARNING',
    trigger_mode='SCHEDULED',
    schedule_cron='0 */6 * * *',  # Every 6 hours
    is_active=True,
)
```

**Workflow Bottleneck Detection:**

```python
AutomationRule.objects.create(
    name="Evaluation Queue Bottleneck",
    rule_code="WORKFLOW_EVAL_QUEUE_BOTTLENECK",
    description="Alert when bits sit in eval queue > 2x average time",
    rule_scope='WORKFLOW',
    target_model='planning.BitWorkflowPosition',
    condition_definition={
        "type": "custom",
        "expression": "obj.is_current and obj.stage.stage_code == 'EVAL_QUEUE' and obj.time_in_stage_hours > (obj.stage.average_duration_hours * 2.0)"
    },
    action_type='CREATE_ALERT',
    action_config={
        "alert_type": "BOTTLENECK",
        "priority": "HIGH"
    },
    severity='CRITICAL',
    trigger_mode='SCHEDULED',
    schedule_cron='*/15 * * * *',  # Every 15 minutes
    is_active=True,
)
```

### 6. Running Rules Manually

```python
from floor_app.operations.analytics.models import AutomationRule

# Get rule
rule = AutomationRule.objects.get(rule_code='INV_LOW_STOCK_ENO_RECLAIM')

# Execute rule
execution = rule.execute()

# Check result
if execution.was_triggered:
    print(f"Rule triggered: {execution.comment}")
    print(f"Context: {execution.context_data}")
```

### 7. Querying Analytics

```python
from floor_app.operations.analytics.models import AppEvent, InformationRequest
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

# Most viewed pages (last 30 days)
thirty_days_ago = timezone.now() - timedelta(days=30)
top_pages = AppEvent.objects.filter(
    timestamp__gte=thirty_days_ago,
    event_type='PAGE_VIEW'
).values('view_name').annotate(
    views=Count('id')
).order_by('-views')[:10]

# Email reduction stats
stats = InformationRequest.get_email_reduction_stats(
    start_date=thirty_days_ago
)
print(f"Email Reduction: {stats['reduction_percentage']}%")
print(f"Total Requests: {stats['total_requests']}")
print(f"Now Covered: {stats['covered_requests']}")

# Top uncovered requests (prioritize development)
uncovered = InformationRequest.get_top_uncovered_requests(limit=10)
for req in uncovered:
    print(f"{req.summary} - Asked {req.repeat_count} times")
```

---

## Test Data Generation

### Management Command: generate_analytics_test_data

```bash
python manage.py generate_analytics_test_data --events=1000 --requests=50 --rules=10
```

Creates:
- 1000 realistic app events (page views, reports, actions)
- 50 information requests (various categories, some repeated)
- 10 automation rules (various scopes, some triggered)
- Event summaries (hourly/daily)
- Request trends (daily/weekly)
- Rule executions (triggered and not triggered)

### Management Command: create_rule_templates

```bash
python manage.py create_rule_templates
```

Creates pre-configured rule templates:
- Stock alert templates (various thresholds)
- Workflow delay templates
- Quality issue templates
- Planning bottleneck templates

### Management Command: run_rules_manually

```bash
# Run all active rules
python manage.py run_rules_manually

# Run specific scope
python manage.py run_rules_manually --scope=INVENTORY

# Run specific rule
python manage.py run_rules_manually --rule-code=INV_LOW_STOCK_ENO_RECLAIM
```

---

## Business Use Cases

### Use Case 1: Email Reduction Measurement

**Scenario:** Management wants to prove ROI of new Bit Status Tracker feature.

**Before Feature:**
1. Log all "What's the status of bit X?" requests
2. Track: 50 status inquiries per month (channel=EMAIL/PHONE)
3. Category: STATUS

**After Feature:**
1. Build Bit Status Tracker page
2. Mark all STATUS requests as covered:
   ```python
   InformationRequest.objects.filter(
       request_category='STATUS',
       summary__icontains='status'
   ).update(
       is_now_covered_by_system=True,
       covered_by_view_name='bit_status_tracker',
       covered_by_url='/production/bits/status/'
   )
   ```
3. Monitor new STATUS requests per month
4. Email Reduction Dashboard shows:
   - Before: 50 requests/month
   - After: 10 requests/month
   - **Reduction: 80%**

**ROI Calculation:**
- Average time per request: 10 minutes
- 40 requests saved × 10 min = 400 min/month = 6.7 hours/month
- At $50/hour = **$335/month savings** = **$4,020/year**

### Use Case 2: Feature Prioritization

**Scenario:** Limited development resources. Which features to build first?

**Analysis:**
1. Query top uncovered requests:
   ```python
   uncovered = InformationRequest.get_top_uncovered_requests(limit=20)
   ```

2. Results show:
   - "Cutter stock report" - Asked 25 times
   - "Weekly production plan export" - Asked 18 times
   - "Quality inspection checklist" - Asked 12 times
   - "Maintenance schedule view" - Asked 3 times

**Decision:** Build cutter stock report first (highest demand).

**Validation:**
1. Build feature
2. Mark requests as covered
3. Track usage: `AppEvent.objects.filter(view_name='cutter_stock_report').count()`
4. Confirm: High usage + request reduction = successful feature

### Use Case 3: Proactive Inventory Management

**Scenario:** Prevent stockouts by catching low stock before it's critical.

**Implementation:**
1. Create rule: "Alert when cutter stock < BOM requirement for planned jobs"
   ```python
   AutomationRule.objects.create(
       name="Cutter Stock vs BOM Requirement",
       rule_code="INV_STOCK_VS_BOM",
       condition_definition={
           "type": "field_comparison",
           "field1": "quantity_on_hand",
           "operator": "<",
           "field2": "bom_requirement_next_week"
       },
       action_type='SEND_NOTIFICATION',
       action_config={
           "recipients": ["purchasing@company.com"],
           "subject": "Stock Alert: {cutter_type}",
           "message": "Current stock ({current}) below BOM requirement ({required}) for next week's jobs"
       }
   )
   ```

2. Rule runs every 6 hours
3. Alerts sent before stockout occurs
4. Purchasing orders ahead of time

**Result:** Zero stockouts, reduced rush orders, better planning.

### Use Case 4: Bottleneck Detection

**Scenario:** Production manager wants to know where workflow slows down.

**Implementation:**
1. Create rule: "Alert when stage exceeds average duration by 1.5x"
2. Integrates with BitWorkflowPosition (Visual Planning Dashboard)
3. Rule triggers when bits sit too long in any stage

**Analysis:**
1. Check rule executions:
   ```python
   bottlenecks = AutomationRuleExecution.objects.filter(
       rule__rule_code='WORKFLOW_BOTTLENECK',
       was_triggered=True,
       executed_at__gte=thirty_days_ago
   )
   ```

2. Group by stage:
   - EVAL_QUEUE: 45 triggers (most common bottleneck)
   - REPAIR_QUEUE: 12 triggers
   - QC: 3 triggers

**Action:** Hire additional evaluator to address EVAL_QUEUE bottleneck.

**Validation:** After hiring, EVAL_QUEUE bottleneck triggers drop from 45/month to 10/month.

### Use Case 5: Feature Adoption Tracking

**Scenario:** Built new "Visual Planning Board" feature. Is anyone using it?

**Tracking:**
```python
# Daily usage of visual board
daily_usage = AppEvent.objects.filter(
    view_name='visual_planning_board',
    timestamp__gte=thirty_days_ago
).extra(select={'date': 'DATE(timestamp)'}).values('date').annotate(
    unique_users=Count('user', distinct=True),
    total_views=Count('id')
)
```

**Results:**
- Week 1: 3 unique users, 15 views
- Week 2: 8 unique users, 45 views
- Week 3: 12 unique users, 120 views
- Week 4: 15 unique users, 200 views

**Conclusion:** Strong adoption curve. Feature is valuable.

**Opposite Example:**
"Advanced Cutter Analysis Tool" - 0 users after 2 months.
**Action:** Remove from menu or simplify UI.

---

## Dashboard Wireframes

### Main Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Analytics & KPI Dashboard                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│ │ Total     │  │ Email     │  │ Active    │  │ Rules     │ │
│ │ Page Views│  │ Reduction │  │ Users     │  │ Triggered │ │
│ │  12,543   │  │   45%     │  │    23     │  │    156    │ │
│ └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
│                                                               │
│ ┌──────────────────────────────┬────────────────────────────┐│
│ │ Usage Trend (Last 30 Days)   │ Top 10 Pages               ││
│ │                              │                            ││
│ │  [Line Chart]                │ 1. Job Card Detail  234    ││
│ │                              │ 2. Cutter Inventory 189    ││
│ │                              │ 3. Bit Status       145    ││
│ │                              │ 4. Planning Board   112    ││
│ │                              │ 5. Evaluation Grid   98    ││
│ └──────────────────────────────┴────────────────────────────┘│
│                                                               │
│ ┌──────────────────────────────┬────────────────────────────┐│
│ │ Request Trend                │ Top Uncovered Requests     ││
│ │                              │                            ││
│ │  [Stacked Bar: Covered/Open] │ 1. Production plan   (15x) ││
│ │                              │ 2. Stock report      (12x) ││
│ │                              │ 3. QC checklist       (8x) ││
│ └──────────────────────────────┴────────────────────────────┘│
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Recent Rule Triggers                                    │ │
│ │                                                         │ │
│ │ ⚠️  Low Stock Alert: ENO Reclaimed         2 hours ago │ │
│ │ 🚨  Eval Queue Bottleneck                  4 hours ago │ │
│ │ ℹ️  Weekly Summary Generated               Yesterday   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Event Storage

- AppEvent table will grow large (1000s of records per day)
- **Solution:**
  - Keep raw events for 90 days only (cleanup task)
  - Use EventSummary for long-term trends (aggregated data)
  - Add database indexes on frequently queried fields

### Rule Execution

- Running rules on large querysets can be slow
- **Solution:**
  - Limit queryset size (default 1000 objects)
  - Use select_related/prefetch_related in evaluator
  - Run rules async via Celery
  - Set min_interval_seconds to avoid too-frequent execution

### Async Logging

- Synchronous event logging adds latency to every request
- **Solution:**
  - Enable ANALYTICS_ASYNC_LOGGING = True
  - Use Celery for background logging
  - Middleware adds <5ms overhead with async logging

---

## Security Considerations

### Rule Engine Safety

- **No arbitrary code execution** - All conditions parsed safely
- **Whitelist approach** for custom expressions
- **Approval workflow** - Rules must be approved before activation
- **Action whitelisting** - RUN_SCRIPT only runs whitelisted commands

### Event Data Privacy

- **PII considerations** - Events may contain user data
- **Solution:**
  - Don't log sensitive query parameters (passwords, tokens)
  - Exclude sensitive paths (payment, auth endpoints)
  - Anonymize old events before long-term storage

### Information Request Data

- May contain confidential customer information
- **Solution:**
  - Restrict access to authorized users only
  - Use Django permissions for CRUD operations
  - Audit log who views/edits requests

---

## Next Steps

1. ✅ Backend complete (models, rule engine, middleware, decorators)
2. 🔄 Create views (in progress)
3. 🔄 Create templates with charts
4. 🔄 Create management commands
5. 🔄 Generate test data
6. ⏳ Run migrations
7. ⏳ Add to navigation
8. ⏳ Deploy and train users

---

## Support & Documentation

For questions or issues:
- Check this guide first
- Review model docstrings (comprehensive inline documentation)
- Check admin interface (all models registered)
- Run management commands with --help flag

## Summary

This analytics system provides **measurable business value**:

✅ **Email Reduction:** Track and measure shift from email → system
✅ **Feature Prioritization:** Data-driven development decisions
✅ **Proactive Operations:** Catch issues before they escalate
✅ **Usage Insights:** Know what's used vs ignored
✅ **ROI Proof:** Quantify digital transformation value

**Foundation for data-driven operations management.**

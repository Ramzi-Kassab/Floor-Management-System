# Advanced Features Documentation

**Last Updated:** November 18, 2025

This document covers Options 5, 7, 8, and 9.

---

## Option 7: Advanced Reporting System

### Features
- Dynamic report builder with filtering and grouping
- Scheduled reports with email delivery
- Report template library
- Multi-format export (CSV, Excel, PDF, HTML)
- Custom aggregations (count, sum, avg, max, min)

### Usage

**Build Custom Report:**
```python
from core.reports import ReportBuilder
from myapp.models import MyModel

# Build report
report = ReportBuilder(MyModel, fields=['id', 'name', 'status']) \
    .filter(status='ACTIVE', created_at__gte=start_date) \
    .group('status') \
    .aggregate('id', func='count', label='count') \
    .sort('-count')

# Execute
results = report.execute()
```

**Register Report Template:**
```python
from core.reports import register_report_template, ReportBuilder

@register_report_template(
    name='daily_sales',
    description='Daily sales summary',
    schedule={'schedule_type': 'daily', 'hour': 8}
)
def daily_sales_report():
    return ReportBuilder(SalesOrder) \
        .filter(created_at__gte=today) \
        .aggregate('total', func='sum')
```

**Schedule Report Email:**
```python
from core.reports import ScheduledReport, REPORT_TEMPLATES

template = REPORT_TEMPLATES['daily_sales']
scheduled = ScheduledReport(
    name='Daily Sales Email',
    template=template,
    schedule_config={'schedule_type': 'daily', 'hour': 9},
    recipients=['manager@company.com'],
    enabled=True
)

scheduled.register_schedule()
```

---

## Option 8: Analytics & Business Intelligence

### Features
- KPI tracking with trend analysis
- Performance metrics calculation
- Moving averages
- Linear forecasting
- Growth rate analysis
- Efficiency metrics

### Usage

**Track KPIs:**
```python
from core.analytics import KPITracker

# Calculate KPI for last 30 days
kpi = KPITracker.calculate_kpi(
    model=JobCard,
    metric_field='completion_time',
    filters={'status': 'COMPLETED'},
    period_days=30
)

# Results include:
# - current period stats
# - previous period stats  
# - change percentages
```

**Get Trend Data:**
```python
# Get daily trend for last 30 days
trend = KPITracker.get_trend(
    model=JobCard,
    date_field='created_at',
    period_days=30,
    interval='day'
)

# Returns: [{'period': '2025-11-01', 'count': 15}, ...]
```

**Performance Metrics:**
```python
from core.analytics import PerformanceMetrics

# Calculate efficiency
efficiency = PerformanceMetrics.calculate_efficiency(
    completed=85,
    total=100
)  # Returns: 85.0

# Growth rate
growth = PerformanceMetrics.calculate_growth_rate(
    current=120,
    previous=100
)  # Returns: 20.0

# Moving average
ma = PerformanceMetrics.moving_average(
    data_points=[10, 12, 15, 14, 16, 18, 20],
    window=7
)

# Linear forecast
forecast = PerformanceMetrics.forecast_linear(
    historical_data=[10, 12, 15, 17, 20],
    periods=7  # Forecast next 7 periods
)
```

---

## Option 9: Mobile Optimization & PWA

### Features
- Progressive Web App (PWA) configuration
- Offline capability support
- Service worker integration
- Mobile device detection
- Touch-optimized UI helpers
- App-like experience

### PWA Setup

**1. Add manifest route** (in urls.py):
```python
from core.mobile import PWAConfig

path('manifest.json', lambda r: JsonResponse(PWAConfig.get_manifest()))
```

**2. Add service worker** (in base template):
```html
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('SW registered'))
        .catch(err => console.error('SW error', err));
}
</script>
```

**3. Device Detection:**
```python
from core.mobile import MobileDetector

# In view
def my_view(request):
    is_mobile = MobileDetector.is_mobile(request)
    device_type = MobileDetector.get_device_type(request)
    
    # Use mobile template if needed
    template = 'mobile/page.html' if is_mobile else 'page.html'
    return render(request, template, context)
```

### PWA Manifest
The system generates a complete PWA manifest with:
- App name and description
- Icons (192x192, 512x512)
- Display mode (standalone)
- Theme colors
- Shortcuts
- Categories

---

## Option 5: Real-time Updates

### Features
- Real-time event delivery framework
- User presence tracking
- Live notifications
- Dashboard updates
- Group messaging

**Note:** Full WebSocket implementation requires Django Channels.
This provides the framework and cache-based implementation.

### Usage

**Send Real-time Event:**
```python
from core.realtime import RealtimeChannel

# Send to specific user
RealtimeChannel.send_to_user(
    user_id=123,
    event_type='notification',
    data={'title': 'New Message', 'count': 5}
)

# Send to group
RealtimeChannel.send_to_group(
    group_name='production_team',
    event_type='update',
    data={'status': 'completed'}
)

# Broadcast to all
RealtimeChannel.broadcast(
    event_type='system',
    data={'message': 'System maintenance in 10 minutes'}
)
```

**Get Events (Polling):**
```python
# In JavaScript (polling approach)
setInterval(async () => {
    const response = await fetch('/api/realtime/events/');
    const events = await response.json();
    
    events.forEach(event => {
        if (event.type === 'notification') {
            showNotification(event.data);
        }
    });
}, 5000);  // Poll every 5 seconds
```

**Presence Tracking:**
```python
from core.realtime import PresenceTracker

# Mark user online (in middleware or login)
PresenceTracker.user_online(user.id)

# Mark offline (in logout)
PresenceTracker.user_offline(user.id)

# Check status
is_online = PresenceTracker.is_user_online(user.id)

# Get all online users
online_users = PresenceTracker.get_online_users()
```

---

## Integration Examples

### Dashboard with Real-time KPIs
```python
# View
def dashboard(request):
    # Get KPIs
    production_kpi = KPITracker.calculate_kpi(JobCard, 'completion_time')
    sales_kpi = KPITracker.calculate_kpi(SalesOrder, 'total_amount')
    
    # Get trends
    production_trend = KPITracker.get_trend(JobCard, period_days=30)
    
    # Check online team
    online_users = PresenceTracker.get_online_users()
    
    context = {
        'production_kpi': production_kpi,
        'sales_kpi': sales_kpi,
        'production_trend': production_trend,
        'online_users': online_users
    }
    
    return render(request, 'dashboard.html', context)
```

### Mobile-Optimized Report
```python
def mobile_report(request):
    # Build report
    report = ReportBuilder(JobCard) \
        .filter(status='ACTIVE') \
        .group('department') \
        .aggregate('id', func='count')
    
    results = report.execute()
    
    # Use mobile template if needed
    if MobileDetector.is_mobile(request):
        return render(request, 'reports/mobile.html', {'data': results})
    else:
        return render(request, 'reports/desktop.html', {'data': results})
```

---

## Files Created

### Option 7 - Reporting
- `core/reports.py` (230 lines)
  - ReportBuilder
  - ReportTemplate
  - ScheduledReport
  - Report decorators

### Option 8 - Analytics
- `core/analytics.py` (180 lines)
  - KPITracker
  - PerformanceMetrics
  - Trend analysis
  - Forecasting

### Option 9 - Mobile
- `core/mobile.py` (100 lines)
  - PWAConfig
  - MobileDetector
  - Service worker

### Option 5 - Real-time
- `core/realtime.py` (130 lines)
  - RealtimeChannel
  - PresenceTracker
  - Event management

**Total: ~640 lines**

---

## Best Practices

### Reporting
1. Use ReportBuilder for dynamic reports
2. Register templates for reusable reports
3. Schedule resource-intensive reports for off-hours
4. Cache report results when possible

### Analytics
1. Calculate KPIs during off-peak hours
2. Use caching for dashboard metrics
3. Limit historical data ranges for performance
4. Aggregate data at database level

### Mobile
1. Test on actual mobile devices
2. Implement responsive design
3. Minimize data transfer for mobile
4. Use progressive enhancement

### Real-time
1. For production, use Django Channels
2. Implement fallback to polling
3. Limit event payload size
4. Clean up old events regularly

---

## Future Enhancements

### Reporting
- Visual report designer UI
- More export formats
- Report versioning
- Report sharing

### Analytics
- Machine learning integration
- Anomaly detection
- Predictive models
- Custom dashboards

### Mobile
- Native mobile apps
- Push notifications
- Offline sync
- Biometric authentication

### Real-time
- Full WebSocket implementation
- Video/voice calls
- Screen sharing
- Collaborative editing

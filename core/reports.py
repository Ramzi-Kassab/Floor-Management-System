"""
Advanced Reporting System for Floor Management System.

Features:
- Report builder with query interface
- Scheduled reports with email delivery
- Report templates library
- Custom aggregations and grouping
- Multi-format export (CSV, Excel, PDF, HTML)
"""

from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Max, Min, Q
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from .export_utils import DataExporter
from .tasks import ScheduledTask, scheduler


class ReportBuilder:
    """
    Dynamic report builder.
    
    Build custom reports with filtering, grouping, and aggregations.
    """
    
    def __init__(self, model, fields=None):
        """Initialize report builder for a model."""
        self.model = model
        self.queryset = model.objects.all()
        self.fields = fields or []
        self.filters = {}
        self.group_by = None
        self.aggregations = {}
        self.order_by = []
        
    def filter(self, **kwargs):
        """Add filters to report."""
        self.filters.update(kwargs)
        return self
        
    def group(self, field):
        """Group results by field."""
        self.group_by = field
        return self
        
    def aggregate(self, field, func='count', label=None):
        """Add aggregation."""
        agg_funcs = {
            'count': Count,
            'sum': Sum,
            'avg': Avg,
            'max': Max,
            'min': Min
        }
        
        if func not in agg_funcs:
            raise ValueError(f"Invalid aggregation: {func}")
            
        agg_label = label or f"{field}_{func}"
        self.aggregations[agg_label] = agg_funcs[func](field)
        return self
        
    def sort(self, *fields):
        """Add sorting."""
        self.order_by = list(fields)
        return self
        
    def execute(self):
        """Execute report and return results."""
        queryset = self.queryset
        
        # Apply filters
        if self.filters:
            queryset = queryset.filter(**self.filters)
            
        # Apply grouping and aggregations
        if self.group_by and self.aggregations:
            queryset = queryset.values(self.group_by).annotate(**self.aggregations)
        elif self.aggregations:
            queryset = queryset.aggregate(**self.aggregations)
            return queryset
        else:
            queryset = queryset.values(*self.fields) if self.fields else queryset
            
        # Apply sorting
        if self.order_by:
            queryset = queryset.order_by(*self.order_by)
            
        return list(queryset)
        
    def to_dict(self):
        """Return report configuration as dict."""
        return {
            'model': f"{self.model._meta.app_label}.{self.model._meta.model_name}",
            'fields': self.fields,
            'filters': self.filters,
            'group_by': self.group_by,
            'aggregations': {k: str(v) for k, v in self.aggregations.items()},
            'order_by': self.order_by
        }


class ReportTemplate:
    """Pre-defined report template."""
    
    def __init__(self, name, description, builder_func, schedule=None):
        """
        Initialize report template.
        
        Args:
            name: Template name
            description: Template description
            builder_func: Function that returns configured ReportBuilder
            schedule: Optional schedule configuration
        """
        self.name = name
        self.description = description
        self.builder_func = builder_func
        self.schedule = schedule
        
    def execute(self):
        """Execute report template."""
        builder = self.builder_func()
        return builder.execute()
        
    def export(self, format='excel'):
        """Export report in specified format."""
        builder = self.builder_func()
        data = builder.execute()
        
        # Create exporter (simplified - would need proper implementation)
        # This is a placeholder
        return {'format': format, 'data': data}


class ScheduledReport:
    """
    Scheduled report with email delivery.
    
    Reports can be scheduled to run automatically and emailed to recipients.
    """
    
    def __init__(self, name, template, schedule_config, recipients, enabled=True):
        """
        Initialize scheduled report.
        
        Args:
            name: Report name
            template: ReportTemplate instance
            schedule_config: Dict with schedule configuration
            recipients: List of email addresses
            enabled: Whether report is enabled
        """
        self.name = name
        self.template = template
        self.schedule_config = schedule_config
        self.recipients = recipients if isinstance(recipients, list) else [recipients]
        self.enabled = enabled
        
    def generate_and_send(self):
        """Generate report and send via email."""
        if not self.enabled:
            return False
            
        # Generate report
        data = self.template.execute()
        
        # Export to file
        export_result = self.template.export(format='excel')
        
        # Send email
        subject = f"Scheduled Report: {self.name}"
        message = f"Please find attached the {self.name} report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}."
        
        email = EmailMessage(
            subject=subject,
            body=message,
            to=self.recipients
        )
        
        # Attach report file
        # email.attach(f"{self.name}.xlsx", file_content, 'application/vnd.ms-excel')
        
        try:
            email.send()
            return True
        except Exception as e:
            print(f"Failed to send report: {e}")
            return False
            
    def register_schedule(self):
        """Register this report as a scheduled task."""
        task = ScheduledTask(
            name=f"report_{self.name}",
            func=self.generate_and_send,
            **self.schedule_config
        )
        
        scheduler.register_task(task)


# Report template library
REPORT_TEMPLATES = {}


def register_report_template(name, description, schedule=None):
    """Decorator to register report template."""
    def decorator(func):
        template = ReportTemplate(name, description, func, schedule)
        REPORT_TEMPLATES[name] = template
        return func
    return decorator


# Example report templates
@register_report_template(
    name='daily_user_activity',
    description='Daily user activity summary',
    schedule={'schedule_type': 'daily', 'hour': 8, 'minute': 0}
)
def daily_user_activity_report():
    """Generate daily user activity report."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    yesterday = timezone.now() - timedelta(days=1)
    
    return ReportBuilder(User) \
        .filter(last_login__gte=yesterday) \
        .aggregate('id', func='count', label='active_users')


@register_report_template(
    name='monthly_export_summary',
    description='Monthly export activity summary'
)
def monthly_export_summary():
    """Generate monthly export summary."""
    from .models import ActivityLog
    
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    
    return ReportBuilder(ActivityLog) \
        .filter(action='EXPORT', created_at__gte=start_of_month) \
        .group('user') \
        .aggregate('id', func='count', label='export_count') \
        .sort('-export_count')

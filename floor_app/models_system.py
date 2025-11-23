"""
System Models for Floor App.

This module contains models for system-wide features:
- Audit Logs
- API Keys
- Webhooks
- Support Tickets
- Help Articles
- Dashboard Widgets
- User Activity

Note: Notification models already exist in floor_app.operations.notifications.models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import URLValidator
import secrets


# ========== AUDIT LOGS ==========

class AuditLog(models.Model):
    """System audit trail for compliance and monitoring."""

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]

    MODULE_CHOICES = [
        ('production', 'Production'),
        ('quality', 'Quality'),
        ('inventory', 'Inventory'),
        ('hr', 'HR'),
        ('sales', 'Sales'),
        ('analytics', 'Analytics'),
        ('system', 'System'),
        ('admin', 'Admin'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    object_type = models.CharField(max_length=100)  # e.g., 'ProductionJob', 'User'
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    changes = models.JSONField(blank=True, null=True)  # Store before/after state
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'module']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.description[:50]}"

    @classmethod
    def log_action(cls, user, action, module, object_type, description, request=None, **kwargs):
        """Helper method to create audit log entries."""
        ip_address = None
        user_agent = ''

        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            action=action,
            module=module,
            object_type=object_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )

    @staticmethod
    def get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ========== API MANAGEMENT ==========

class APIKey(models.Model):
    """API keys for external integrations."""

    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Write Only'),
        ('full', 'Full Access'),
        ('custom', 'Custom Permissions'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True, db_index=True)
    prefix = models.CharField(max_length=8)  # First 8 chars for identification
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='read')
    rate_limit = models.IntegerField(default=10000, help_text="Requests per hour")
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(blank=True, null=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
            self.prefix = self.key[:8]
        super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        return f"fms_{secrets.token_urlsafe(40)}"

    def regenerate_key(self):
        """Regenerate the API key."""
        self.key = self.generate_key()
        self.prefix = self.key[:8]
        self.save()
        return self.key

    def record_usage(self):
        """Record API key usage."""
        self.last_used = timezone.now()
        self.usage_count += 1
        self.save(update_fields=['last_used', 'usage_count'])

    def is_valid(self):
        """Check if API key is valid and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class Webhook(models.Model):
    """Webhooks for event notifications."""

    EVENT_CHOICES = [
        ('job_created', 'Production Job Created'),
        ('job_completed', 'Production Job Completed'),
        ('inspection_passed', 'Quality Inspection Passed'),
        ('inspection_failed', 'Quality Inspection Failed'),
        ('low_stock', 'Low Stock Alert'),
        ('user_login', 'User Login'),
        ('custom', 'Custom Event'),
    ]

    name = models.CharField(max_length=255)
    url = models.URLField(validators=[URLValidator()])
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    secret_key = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30, help_text="Timeout in seconds")
    last_triggered = models.DateTimeField(blank=True, null=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.event_type}"

    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def trigger(self, payload):
        """Trigger webhook with payload."""
        # TODO: Implement async webhook delivery
        self.last_triggered = timezone.now()
        self.save()


class WebhookLog(models.Model):
    """Log of webhook deliveries."""

    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='logs')
    payload = models.JSONField()
    response_code = models.IntegerField(blank=True, null=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    triggered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"{self.webhook.name} - {'Success' if self.success else 'Failed'} - {self.triggered_at}"


# ========== SUPPORT SYSTEM ==========

class SupportTicket(models.Model):
    """Support ticket system."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    CATEGORY_CHOICES = [
        ('technical', 'Technical Issue'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('account', 'Account Access'),
        ('billing', 'Billing Question'),
        ('training', 'Training Request'),
        ('integration', 'Integration Support'),
        ('other', 'Other'),
    ]

    ticket_id = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['ticket_id']),
        ]

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = self.generate_ticket_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_ticket_id():
        """Generate unique ticket ID."""
        import random
        return f"#{random.randint(10000, 99999)}"


class SupportTicketReply(models.Model):
    """Replies to support tickets."""

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to {self.ticket.ticket_id} by {self.user.username}"


# ========== HELP SYSTEM ==========

class HelpCategory(models.Model):
    """Categories for help articles."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-question-circle')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Help Categories'

    def __str__(self):
        return self.name


class HelpArticle(models.Model):
    """Help center articles."""

    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=True)
    views = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increment_views(self):
        """Increment article view count."""
        self.views += 1
        self.save(update_fields=['views'])


# ========== DASHBOARD CUSTOMIZATION ==========

class DashboardWidget(models.Model):
    """User dashboard widgets."""

    WIDGET_TYPE_CHOICES = [
        ('stats', 'Statistics Card'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('recent', 'Recent Items'),
        ('alerts', 'Alerts'),
        ('calendar', 'Calendar'),
        ('custom', 'Custom Widget'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    config = models.JSONField(default=dict)  # Widget-specific configuration
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=1)
    height = models.IntegerField(default=1)
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user', 'order']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class DashboardLayout(models.Model):
    """Saved dashboard layouts."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_layouts')
    name = models.CharField(max_length=100)
    layout_config = models.JSONField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


# ========== USER THEME PREFERENCES ==========

class UserThemePreference(models.Model):
    """User interface theme and display preferences."""

    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('auto', 'Auto (System)'),
        ('custom', 'Custom Colors'),
    ]

    FONT_SIZE_CHOICES = [
        ('small', 'Small (14px)'),
        ('medium', 'Medium (16px)'),
        ('large', 'Large (18px)'),
        ('x-large', 'Extra Large (20px)'),
    ]

    DENSITY_CHOICES = [
        ('compact', 'Compact'),
        ('comfortable', 'Comfortable'),
        ('spacious', 'Spacious'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='theme_preference')

    # Theme settings
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    high_contrast = models.BooleanField(default=False, help_text='Enable high contrast mode for accessibility')

    # Custom colors (for custom theme)
    primary_color = models.CharField(max_length=7, default='#2563eb', help_text='Primary brand color (hex)')
    accent_color = models.CharField(max_length=7, default='#10b981', help_text='Accent/highlight color (hex)')
    background_color = models.CharField(max_length=7, default='#ffffff', help_text='Main background color (hex)')
    text_color = models.CharField(max_length=7, default='#1f2937', help_text='Primary text color (hex)')

    # Text preferences
    font_size = models.CharField(max_length=20, choices=FONT_SIZE_CHOICES, default='medium')
    font_family = models.CharField(max_length=100, default='system', help_text='Font family preference')
    line_height = models.DecimalField(max_digits=3, decimal_places=1, default=1.5, help_text='Line height multiplier')

    # Layout preferences
    sidebar_collapsed = models.BooleanField(default=False)
    density = models.CharField(max_length=20, choices=DENSITY_CHOICES, default='comfortable')
    show_animations = models.BooleanField(default=True, help_text='Enable UI animations')

    # Accessibility
    reduce_motion = models.BooleanField(default=False, help_text='Reduce motion for accessibility')
    focus_indicators = models.BooleanField(default=True, help_text='Show enhanced focus indicators')
    screen_reader_optimized = models.BooleanField(default=False)

    # Mobile preferences
    mobile_view = models.CharField(max_length=20, default='auto', choices=[
        ('auto', 'Auto Detect'),
        ('mobile', 'Always Mobile'),
        ('desktop', 'Always Desktop'),
    ])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Theme Preference'
        verbose_name_plural = 'User Theme Preferences'

    def __str__(self):
        return f"{self.user.username} - {self.get_theme_display()}"

    def get_css_variables(self):
        """Generate CSS custom properties for this theme."""
        return {
            '--primary-color': self.primary_color,
            '--accent-color': self.accent_color,
            '--color-bg-primary': self.background_color,
            '--color-text-primary': self.text_color,
            '--font-size-base': self.get_font_size_px(),
            '--line-height': str(self.line_height),
            '--spacing-multiplier': self.get_density_multiplier(),
        }

    def get_font_size_px(self):
        """Get font size in pixels."""
        sizes = {'small': '14px', 'medium': '16px', 'large': '18px', 'x-large': '20px'}
        return sizes.get(self.font_size, '16px')

    def get_density_multiplier(self):
        """Get spacing multiplier for density."""
        densities = {'compact': '0.75', 'comfortable': '1', 'spacious': '1.25'}
        return densities.get(self.density, '1')

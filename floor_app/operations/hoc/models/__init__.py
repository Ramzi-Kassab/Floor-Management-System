"""
Hazard Observation Card (HOC) Models

Models for workplace safety hazard observation and tracking system.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin


class HazardCategory(AuditMixin):
    """Categories for hazard observations."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., 'Safety', 'Environmental', 'Quality')"
    )

    description = models.TextField(
        blank=True,
        help_text="Category description"
    )

    color = models.CharField(
        max_length=20,
        default='#FF5722',
        help_text="Color code for UI display"
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon identifier"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Category is active"
    )

    sort_order = models.IntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        db_table = 'hoc_categories'
        verbose_name = 'Hazard Category'
        verbose_name_plural = 'Hazard Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class HazardObservation(AuditMixin):
    """Hazard observation card submitted by employees."""

    SEVERITY_CHOICES = (
        ('LOW', 'Low - Minor issue'),
        ('MEDIUM', 'Medium - Needs attention'),
        ('HIGH', 'High - Immediate action required'),
        ('CRITICAL', 'Critical - Stop work'),
    )

    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ACTION_ASSIGNED', 'Action Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('VERIFIED', 'Verified'),
        ('CLOSED', 'Closed'),
    )

    # Submission Information
    card_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique HOC number (e.g., HOC-2025-0001)"
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_hocs',
        help_text="Employee who submitted the observation"
    )

    submission_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the observation was submitted"
    )

    # Hazard Details
    category = models.ForeignKey(
        HazardCategory,
        on_delete=models.PROTECT,
        related_name='observations',
        help_text="Hazard category"
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        help_text="Severity level of the hazard"
    )

    title = models.CharField(
        max_length=200,
        help_text="Brief title of the observation"
    )

    description = models.TextField(
        help_text="Detailed description of the hazard"
    )

    # Location Information
    location = models.CharField(
        max_length=200,
        help_text="Where the hazard was observed"
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department/area"
    )

    building = models.CharField(
        max_length=100,
        blank=True,
        help_text="Building/facility"
    )

    floor_level = models.CharField(
        max_length=50,
        blank=True,
        help_text="Floor level"
    )

    gps_coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="GPS coordinates if available"
    )

    # Impact Assessment
    potential_consequence = models.TextField(
        blank=True,
        help_text="What could happen if not addressed"
    )

    people_at_risk = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of people potentially at risk"
    )

    # Current State
    immediate_action_taken = models.TextField(
        blank=True,
        help_text="Any immediate action taken by the observer"
    )

    area_isolated = models.BooleanField(
        default=False,
        help_text="Has the area been isolated/cordoned off"
    )

    work_stopped = models.BooleanField(
        default=False,
        help_text="Has work been stopped in the area"
    )

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUBMITTED',
        help_text="Current status of the observation"
    )

    # Review Information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_hocs',
        help_text="Who reviewed this observation"
    )

    reviewed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the observation was reviewed"
    )

    review_comments = models.TextField(
        blank=True,
        help_text="Review comments"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_hocs',
        help_text="Responsible person for corrective action"
    )

    assigned_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the action was assigned"
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target date for completion"
    )

    # Corrective Actions
    corrective_action_plan = models.TextField(
        blank=True,
        help_text="Planned corrective actions"
    )

    corrective_action_taken = models.TextField(
        blank=True,
        help_text="Actual corrective actions taken"
    )

    action_completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When corrective action was completed"
    )

    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_hocs',
        help_text="Who verified the corrective action"
    )

    verified_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the action was verified"
    )

    verification_comments = models.TextField(
        blank=True,
        help_text="Verification comments"
    )

    # Closure
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_hocs',
        help_text="Who closed this observation"
    )

    closed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the observation was closed"
    )

    closure_comments = models.TextField(
        blank=True,
        help_text="Closure comments"
    )

    # Additional Information
    is_repeat_observation = models.BooleanField(
        default=False,
        help_text="Is this a repeat observation"
    )

    related_incident = models.CharField(
        max_length=100,
        blank=True,
        help_text="Related incident number if applicable"
    )

    cost_estimate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost for corrective action"
    )

    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual cost incurred"
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization"
    )

    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional custom fields"
    )

    class Meta:
        db_table = 'hoc_observations'
        verbose_name = 'Hazard Observation'
        verbose_name_plural = 'Hazard Observations'
        ordering = ['-submission_date']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['status', '-submission_date']),
            models.Index(fields=['severity', '-submission_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.card_number} - {self.title}"

    @property
    def is_overdue(self):
        """Check if the observation is overdue."""
        from django.utils import timezone
        if self.due_date and self.status not in ['COMPLETED', 'VERIFIED', 'CLOSED']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_open(self):
        """Calculate days since submission."""
        from django.utils import timezone
        if self.closed_date:
            return (self.closed_date - self.submission_date).days
        return (timezone.now() - self.submission_date).days


class HOCPhoto(AuditMixin):
    """Photos attached to hazard observations."""

    PHOTO_TYPES = (
        ('BEFORE', 'Before - Hazard condition'),
        ('DURING', 'During - Corrective action'),
        ('AFTER', 'After - Completed'),
        ('EVIDENCE', 'Evidence/Documentation'),
    )

    observation = models.ForeignKey(
        HazardObservation,
        on_delete=models.CASCADE,
        related_name='photos',
        help_text="Related hazard observation"
    )

    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPES,
        default='BEFORE',
        help_text="Type of photo"
    )

    photo = models.ImageField(
        upload_to='hoc_photos/%Y/%m/%d/',
        help_text="Photo file"
    )

    thumbnail = models.ImageField(
        upload_to='hoc_photos/thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Thumbnail version"
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Photo caption"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Who uploaded this photo"
    )

    uploaded_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the photo was uploaded"
    )

    sort_order = models.IntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        db_table = 'hoc_photos'
        verbose_name = 'HOC Photo'
        verbose_name_plural = 'HOC Photos'
        ordering = ['observation', 'sort_order', 'uploaded_date']

    def __str__(self):
        return f"Photo for {self.observation.card_number}"


class HOCComment(AuditMixin):
    """Comments and updates on hazard observations."""

    observation = models.ForeignKey(
        HazardObservation,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Related hazard observation"
    )

    comment = models.TextField(
        help_text="Comment text"
    )

    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hoc_comments',
        help_text="Who made this comment"
    )

    comment_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the comment was made"
    )

    is_internal = models.BooleanField(
        default=False,
        help_text="Internal comment (not visible to submitter)"
    )

    class Meta:
        db_table = 'hoc_comments'
        verbose_name = 'HOC Comment'
        verbose_name_plural = 'HOC Comments'
        ordering = ['observation', 'comment_date']

    def __str__(self):
        return f"Comment on {self.observation.card_number} by {self.commented_by}"


class HOCStatusHistory(AuditMixin):
    """Track status changes for audit trail."""

    observation = models.ForeignKey(
        HazardObservation,
        on_delete=models.CASCADE,
        related_name='status_history',
        help_text="Related hazard observation"
    )

    from_status = models.CharField(
        max_length=20,
        choices=HazardObservation.STATUS_CHOICES,
        help_text="Previous status"
    )

    to_status = models.CharField(
        max_length=20,
        choices=HazardObservation.STATUS_CHOICES,
        help_text="New status"
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Who changed the status"
    )

    changed_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the status was changed"
    )

    reason = models.TextField(
        blank=True,
        help_text="Reason for status change"
    )

    class Meta:
        db_table = 'hoc_status_history'
        verbose_name = 'HOC Status History'
        verbose_name_plural = 'HOC Status Histories'
        ordering = ['observation', 'changed_date']

    def __str__(self):
        return f"{self.observation.card_number}: {self.from_status} → {self.to_status}"


class HOCNotificationSettings(AuditMixin):
    """Notification settings for HOC system."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hoc_notification_settings',
        help_text="User"
    )

    notify_on_submission = models.BooleanField(
        default=True,
        help_text="Notify when new HOC is submitted"
    )

    notify_on_assignment = models.BooleanField(
        default=True,
        help_text="Notify when assigned to HOC"
    )

    notify_on_due_date = models.BooleanField(
        default=True,
        help_text="Notify when HOC is approaching due date"
    )

    notify_on_overdue = models.BooleanField(
        default=True,
        help_text="Notify when assigned HOC is overdue"
    )

    notify_on_completion = models.BooleanField(
        default=True,
        help_text="Notify when assigned HOC is completed"
    )

    notify_on_comment = models.BooleanField(
        default=True,
        help_text="Notify when comment is added to my HOC"
    )

    notification_method = models.JSONField(
        default=dict,
        help_text="Notification methods {email: true, push: true, sms: false}"
    )

    class Meta:
        db_table = 'hoc_notification_settings'
        verbose_name = 'HOC Notification Settings'
        verbose_name_plural = 'HOC Notification Settings'

    def __str__(self):
        return f"Notification settings for {self.user.username}"

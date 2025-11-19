"""
Journey Management Models

Models for field operations journey tracking and management.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from floor_app.mixins import AuditMixin


class JourneyPlan(AuditMixin):
    """Journey plan for field operations."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted for Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    RISK_LEVEL_CHOICES = (
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    )

    # Journey Identification
    journey_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique journey ID (e.g., JRN-2025-0001)"
    )

    title = models.CharField(
        max_length=200,
        help_text="Journey title/purpose"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of the journey purpose"
    )

    # Personnel
    traveler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='journeys',
        help_text="Person traveling"
    )

    companions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='accompanied_journeys',
        help_text="Traveling companions"
    )

    # Journey Details
    departure_location = models.CharField(
        max_length=200,
        help_text="Starting location"
    )

    destination = models.CharField(
        max_length=200,
        help_text="Final destination"
    )

    planned_departure_time = models.DateTimeField(
        help_text="Planned departure date/time"
    )

    planned_return_time = models.DateTimeField(
        help_text="Planned return date/time"
    )

    actual_departure_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual departure time"
    )

    actual_return_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual return time"
    )

    # Route Information
    route_description = models.TextField(
        blank=True,
        help_text="Description of the route"
    )

    estimated_distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Estimated distance in kilometers"
    )

    # Vehicle Information
    vehicle_type = models.CharField(
        max_length=50,
        choices=(
            ('COMPANY_VEHICLE', 'Company Vehicle'),
            ('RENTAL', 'Rental Vehicle'),
            ('PERSONAL', 'Personal Vehicle'),
            ('PUBLIC_TRANSPORT', 'Public Transport'),
            ('FLIGHT', 'Flight'),
            ('OTHER', 'Other'),
        ),
        help_text="Type of transportation"
    )

    vehicle_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Vehicle registration/ID number"
    )

    vehicle_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional vehicle details"
    )

    # Risk Assessment
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='LOW',
        help_text="Overall risk level"
    )

    risk_assessment = models.TextField(
        blank=True,
        help_text="Risk assessment notes"
    )

    hazards_identified = models.JSONField(
        default=list,
        blank=True,
        help_text="List of identified hazards"
    )

    mitigation_measures = models.TextField(
        blank=True,
        help_text="Risk mitigation measures"
    )

    # Emergency Information
    emergency_contact_name = models.CharField(
        max_length=100,
        help_text="Emergency contact person"
    )

    emergency_contact_phone = models.CharField(
        max_length=20,
        help_text="Emergency contact phone"
    )

    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text="Relationship to traveler"
    )

    medical_conditions = models.TextField(
        blank=True,
        help_text="Any medical conditions to be aware of"
    )

    # Status and Approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        help_text="Journey status"
    )

    submitted_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submitted for approval"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_journeys',
        help_text="Who approved the journey"
    )

    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approved"
    )

    approval_comments = models.TextField(
        blank=True,
        help_text="Approval/rejection comments"
    )

    # Completion
    completion_notes = models.TextField(
        blank=True,
        help_text="Notes upon completion"
    )

    incidents_reported = models.BooleanField(
        default=False,
        help_text="Were any incidents reported during the journey"
    )

    incident_details = models.TextField(
        blank=True,
        help_text="Details of any incidents"
    )

    # Additional Information
    purpose_category = models.CharField(
        max_length=50,
        choices=(
            ('SITE_VISIT', 'Site Visit'),
            ('CLIENT_MEETING', 'Client Meeting'),
            ('INSPECTION', 'Inspection'),
            ('DELIVERY', 'Delivery'),
            ('TRAINING', 'Training'),
            ('MAINTENANCE', 'Maintenance'),
            ('OTHER', 'Other'),
        ),
        default='OTHER',
        help_text="Purpose category"
    )

    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated journey cost"
    )

    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual journey cost"
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
        db_table = 'journey_plans'
        verbose_name = 'Journey Plan'
        verbose_name_plural = 'Journey Plans'
        ordering = ['-planned_departure_time']
        indexes = [
            models.Index(fields=['journey_number']),
            models.Index(fields=['traveler', 'status']),
            models.Index(fields=['status', '-planned_departure_time']),
            models.Index(fields=['planned_departure_time']),
        ]

    def __str__(self):
        return f"{self.journey_number} - {self.title}"

    @property
    def is_overdue(self):
        """Check if journey is overdue for return."""
        from django.utils import timezone
        if self.status == 'IN_PROGRESS' and self.planned_return_time:
            return timezone.now() > self.planned_return_time
        return False


class JourneyWaypoint(AuditMixin):
    """Waypoints/stops along the journey route."""

    journey = models.ForeignKey(
        JourneyPlan,
        on_delete=models.CASCADE,
        related_name='waypoints',
        help_text="Related journey"
    )

    sequence = models.IntegerField(
        help_text="Order in the journey (1, 2, 3...)"
    )

    location_name = models.CharField(
        max_length=200,
        help_text="Waypoint location name"
    )

    address = models.TextField(
        blank=True,
        help_text="Full address"
    )

    gps_coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="GPS coordinates (lat,lng)"
    )

    planned_arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned arrival time"
    )

    planned_departure_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned departure time"
    )

    actual_arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual arrival time"
    )

    actual_departure_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual departure time"
    )

    purpose = models.TextField(
        blank=True,
        help_text="Purpose of this stop"
    )

    contact_person = models.CharField(
        max_length=100,
        blank=True,
        help_text="Contact person at this location"
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    completed = models.BooleanField(
        default=False,
        help_text="Waypoint completed"
    )

    class Meta:
        db_table = 'journey_waypoints'
        verbose_name = 'Journey Waypoint'
        verbose_name_plural = 'Journey Waypoints'
        ordering = ['journey', 'sequence']
        unique_together = [['journey', 'sequence']]

    def __str__(self):
        return f"{self.journey.journey_number} - Stop {self.sequence}: {self.location_name}"


class JourneyCheckIn(AuditMixin):
    """Check-in/check-out records at waypoints."""

    CHECK_TYPE_CHOICES = (
        ('DEPARTURE', 'Departure Check'),
        ('ARRIVAL', 'Arrival Check'),
        ('WAYPOINT', 'Waypoint Check'),
        ('RETURN', 'Return Check'),
    )

    journey = models.ForeignKey(
        JourneyPlan,
        on_delete=models.CASCADE,
        related_name='check_ins',
        help_text="Related journey"
    )

    waypoint = models.ForeignKey(
        JourneyWaypoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_ins',
        help_text="Related waypoint (if applicable)"
    )

    check_type = models.CharField(
        max_length=20,
        choices=CHECK_TYPE_CHOICES,
        help_text="Type of check-in"
    )

    check_time = models.DateTimeField(
        auto_now_add=True,
        help_text="When check-in was made"
    )

    location_name = models.CharField(
        max_length=200,
        help_text="Location name"
    )

    gps_coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="GPS coordinates at check-in"
    )

    notes = models.TextField(
        blank=True,
        help_text="Check-in notes"
    )

    vehicle_odometer = models.IntegerField(
        null=True,
        blank=True,
        help_text="Vehicle odometer reading"
    )

    fuel_level = models.CharField(
        max_length=20,
        blank=True,
        choices=(
            ('FULL', 'Full'),
            ('3/4', '3/4'),
            ('1/2', '1/2'),
            ('1/4', '1/4'),
            ('LOW', 'Low'),
        ),
        help_text="Fuel level"
    )

    all_safe = models.BooleanField(
        default=True,
        help_text="Everything safe and as expected"
    )

    issues_reported = models.TextField(
        blank=True,
        help_text="Any issues to report"
    )

    photo = models.ImageField(
        upload_to='journey_checkins/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Optional photo at check-in"
    )

    class Meta:
        db_table = 'journey_check_ins'
        verbose_name = 'Journey Check-In'
        verbose_name_plural = 'Journey Check-Ins'
        ordering = ['journey', 'check_time']

    def __str__(self):
        return f"{self.journey.journey_number} - {self.get_check_type_display()} at {self.check_time}"


class JourneyDocument(AuditMixin):
    """Documents attached to journeys."""

    DOCUMENT_TYPES = (
        ('ROUTE_MAP', 'Route Map'),
        ('RISK_ASSESSMENT', 'Risk Assessment'),
        ('PERMIT', 'Permit/Authorization'),
        ('INSURANCE', 'Insurance Document'),
        ('VEHICLE_DOCS', 'Vehicle Documents'),
        ('OTHER', 'Other'),
    )

    journey = models.ForeignKey(
        JourneyPlan,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Related journey"
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        help_text="Type of document"
    )

    title = models.CharField(
        max_length=200,
        help_text="Document title"
    )

    file = models.FileField(
        upload_to='journey_documents/%Y/%m/%d/',
        help_text="Document file"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Who uploaded the document"
    )

    uploaded_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Upload date"
    )

    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    class Meta:
        db_table = 'journey_documents'
        verbose_name = 'Journey Document'
        verbose_name_plural = 'Journey Documents'
        ordering = ['journey', 'document_type', 'title']

    def __str__(self):
        return f"{self.journey.journey_number} - {self.title}"


class JourneyStatusHistory(AuditMixin):
    """Track status changes for audit trail."""

    journey = models.ForeignKey(
        JourneyPlan,
        on_delete=models.CASCADE,
        related_name='status_history',
        help_text="Related journey"
    )

    from_status = models.CharField(
        max_length=20,
        choices=JourneyPlan.STATUS_CHOICES,
        help_text="Previous status"
    )

    to_status = models.CharField(
        max_length=20,
        choices=JourneyPlan.STATUS_CHOICES,
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
        help_text="When status was changed"
    )

    reason = models.TextField(
        blank=True,
        help_text="Reason for change"
    )

    class Meta:
        db_table = 'journey_status_history'
        verbose_name = 'Journey Status History'
        verbose_name_plural = 'Journey Status Histories'
        ordering = ['journey', 'changed_date']

    def __str__(self):
        return f"{self.journey.journey_number}: {self.from_status} → {self.to_status}"

"""
Meeting Systems Models

Models for meeting room booking and morning meeting management.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.core.models import AuditMixin


# ============================================================================
# Meeting Room Management
# ============================================================================

class MeetingRoom(AuditMixin):
    """Meeting rooms and conference facilities."""

    name = models.CharField(max_length=100, unique=True, help_text="Room name")
    code = models.CharField(max_length=20, unique=True, help_text="Room code/identifier")
    building = models.CharField(max_length=100, blank=True)
    floor_level = models.CharField(max_length=50, blank=True)
    location_details = models.CharField(max_length=200, blank=True)
    capacity = models.IntegerField(help_text="Maximum number of people")
    description = models.TextField(blank=True)

    # Features/Equipment
    has_projector = models.BooleanField(default=False)
    has_whiteboard = models.BooleanField(default=False)
    has_tv = models.BooleanField(default=False)
    has_video_conference = models.BooleanField(default=False)
    has_phone = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=True)
    equipment = models.JSONField(default=list, blank=True, help_text="List of equipment/features")

    # Availability
    is_active = models.BooleanField(default=True)
    is_bookable = models.BooleanField(default=True)
    booking_advance_days = models.IntegerField(default=30, help_text="How many days in advance can be booked")
    min_booking_duration = models.IntegerField(default=30, help_text="Minimum booking duration (minutes)")
    max_booking_duration = models.IntegerField(default=480, help_text="Maximum booking duration (minutes)")

    # Access Control
    requires_approval = models.BooleanField(default=False, help_text="Requires approval before booking")
    allowed_departments = models.JSONField(default=list, blank=True, help_text="Restricted to departments")
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='allowed_rooms')

    # Other
    photo = models.ImageField(upload_to='meeting_rooms/', null=True, blank=True)
    booking_instructions = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'meeting_rooms'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RoomBooking(AuditMixin):
    """Meeting room bookings."""

    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )

    booking_number = models.CharField(max_length=50, unique=True)
    room = models.ForeignKey(MeetingRoom, on_delete=models.PROTECT, related_name='bookings')
    booked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='room_bookings')

    # Meeting Details
    title = models.CharField(max_length=200, help_text="Meeting title/subject")
    description = models.TextField(blank=True)
    meeting_type = models.CharField(max_length=50, choices=(
        ('INTERNAL', 'Internal Meeting'),
        ('CLIENT', 'Client Meeting'),
        ('TRAINING', 'Training'),
        ('INTERVIEW', 'Interview'),
        ('WORKSHOP', 'Workshop'),
        ('OTHER', 'Other'),
    ), default='INTERNAL')

    # Date/Time
    start_time = models.DateTimeField(help_text="Meeting start time")
    end_time = models.DateTimeField(help_text="Meeting end time")
    duration_minutes = models.IntegerField(help_text="Duration in minutes")

    # Participants
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='organized_meetings')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='meeting_participants')
    expected_attendees = models.IntegerField(validators=[MinValueValidator(1)])
    external_participants = models.TextField(blank=True, help_text="External participants (names/emails)")

    # Status & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Setup Requirements
    setup_requirements = models.TextField(blank=True, help_text="Special setup needs")
    catering_required = models.BooleanField(default=False)
    catering_details = models.TextField(blank=True)
    it_support_required = models.BooleanField(default=False)
    it_support_details = models.TextField(blank=True)

    # Check-in/out
    checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    checked_out = models.BooleanField(default=False)
    check_out_time = models.DateTimeField(null=True, blank=True)
    actual_attendees = models.IntegerField(null=True, blank=True)

    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    # Recurring
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict, blank=True, help_text="Recurrence configuration")
    parent_booking = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='recurring_instances')

    # Notes
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        db_table = 'room_bookings'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['room', 'start_time', 'end_time']),
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['booked_by', '-start_time']),
        ]

    def __str__(self):
        return f"{self.booking_number} - {self.title}"

    @property
    def is_conflicting(self):
        """Check if this booking conflicts with others."""
        return RoomBooking.objects.filter(
            room=self.room,
            status__in=['APPROVED', 'CONFIRMED', 'IN_PROGRESS'],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id).exists()


# ============================================================================
# Morning Meeting Management
# ============================================================================

class MorningMeetingGroup(AuditMixin):
    """Groups/teams for morning meetings."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)

    # Meeting Schedule
    meeting_days = models.JSONField(default=list, help_text="Days of week [0=Monday, 6=Sunday]")
    meeting_time = models.TimeField(help_text="Default meeting time")
    typical_duration = models.IntegerField(default=15, help_text="Typical duration (minutes)")
    location = models.CharField(max_length=200, blank=True)
    meeting_room = models.ForeignKey(MeetingRoom, on_delete=models.SET_NULL, null=True, blank=True)

    # Members
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='coordinated_morning_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='morning_meeting_groups')

    # Settings
    is_active = models.BooleanField(default=True)
    attendance_mandatory = models.BooleanField(default=True)
    auto_create_meetings = models.BooleanField(default=True, help_text="Auto-create daily meetings")

    # Topics/Agenda Template
    agenda_template = models.JSONField(default=list, help_text="Standard agenda items")

    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'morning_meeting_groups'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class MorningMeeting(AuditMixin):
    """Individual morning meeting instances."""

    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    meeting_number = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(MorningMeetingGroup, on_delete=models.CASCADE, related_name='meetings')
    meeting_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    actual_duration = models.IntegerField(null=True, blank=True, help_text="Actual duration (minutes)")

    # Leadership
    led_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_morning_meetings')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Agenda
    agenda_items = models.JSONField(default=list, help_text="Agenda items")

    # Notes
    meeting_notes = models.TextField(blank=True)
    key_points = models.JSONField(default=list, blank=True, help_text="Key discussion points")
    action_items = models.JSONField(default=list, blank=True, help_text="Action items with owners")
    safety_moments = models.TextField(blank=True, help_text="Safety moment shared")

    # Metrics
    total_expected = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)

    # Attachments
    photos = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'morning_meetings'
        unique_together = [['group', 'meeting_date']]
        ordering = ['-meeting_date', 'start_time']

    def __str__(self):
        return f"{self.meeting_number} - {self.group.name} on {self.meeting_date}"


class MorningMeetingAttendance(AuditMixin):
    """Attendance tracking for morning meetings."""

    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    )

    meeting = models.ForeignKey(MorningMeeting, on_delete=models.CASCADE, related_name='attendance')
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='morning_meeting_attendance')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    check_in_time = models.TimeField(null=True, blank=True)
    minutes_late = models.IntegerField(null=True, blank=True)

    absence_reason = models.TextField(blank=True)
    excuse_provided = models.BooleanField(default=False)
    excuse_approved = models.BooleanField(default=False)

    # Participation
    contributed = models.BooleanField(default=False, help_text="Actively contributed in meeting")
    contribution_notes = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'morning_meeting_attendance'
        unique_together = [['meeting', 'employee']]
        ordering = ['meeting', 'employee']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.meeting.meeting_number} ({self.status})"


class MeetingActionItem(AuditMixin):
    """Action items from meetings."""

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('OVERDUE', 'Overdue'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )

    # Source
    morning_meeting = models.ForeignKey(MorningMeeting, on_delete=models.CASCADE, null=True, blank=True, related_name='action_items_detail')
    room_booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, null=True, blank=True, related_name='action_items')

    # Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')

    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_action_items')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_action_items')

    # Dates
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    completion_notes = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'meeting_action_items'
        ordering = ['-due_date', 'priority']

    def __str__(self):
        return f"{self.title} → {self.assigned_to.get_full_name()}"

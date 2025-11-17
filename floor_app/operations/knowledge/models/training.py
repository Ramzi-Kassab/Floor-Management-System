"""
Training Center models - Full learning management system with HR integration.
"""
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .article import Article
from .document import Document


class TrainingCourse(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """
    A structured training course with lessons and assessments.
    Integrates with HR qualifications for certification tracking.
    """

    class CourseType(models.TextChoices):
        SAFETY = 'SAFETY', 'Safety Training'
        QUALITY = 'QUALITY', 'Quality Assurance'
        TECHNICAL = 'TECHNICAL', 'Technical Skills'
        OPERATIONAL = 'OPERATIONAL', 'Operational Procedures'
        COMPLIANCE = 'COMPLIANCE', 'Regulatory Compliance'
        ONBOARDING = 'ONBOARDING', 'Employee Onboarding'
        SOFT_SKILLS = 'SOFT_SKILLS', 'Soft Skills'
        LEADERSHIP = 'LEADERSHIP', 'Leadership Development'
        CERTIFICATION = 'CERTIFICATION', 'Professional Certification'
        REFRESHER = 'REFRESHER', 'Refresher Training'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'
        EXPERT = 'EXPERT', 'Expert'

    # Core fields
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique course code, e.g., 'TR-SAF-001'"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    objectives = models.TextField(
        blank=True,
        help_text="Learning objectives (one per line)"
    )
    prerequisites = models.TextField(
        blank=True,
        help_text="Prerequisites for taking this course"
    )

    # Classification
    course_type = models.CharField(
        max_length=20,
        choices=CourseType.choices,
        default=CourseType.TECHNICAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER
    )

    # Timing
    estimated_duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Estimated time to complete in minutes"
    )
    validity_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="How long certification is valid (months). Null = permanent"
    )

    # Organization
    owner_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_courses'
    )

    # Target audience
    target_positions = models.ManyToManyField(
        'hr.Position',
        blank=True,
        related_name='required_courses',
        help_text="Positions that should take this course"
    )
    target_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='required_courses',
        help_text="Departments that should take this course"
    )

    # HR Qualification integration
    grants_qualification = models.ForeignKey(
        'hr.HRQualification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_courses',
        help_text="Qualification granted upon completion"
    )

    # Course requirements
    is_mandatory = models.BooleanField(
        default=False,
        help_text="Mandatory for all employees in target audience"
    )
    requires_assessment = models.BooleanField(
        default=False,
        help_text="Requires passing assessment to complete"
    )
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text="Minimum passing score percentage (0-100)"
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum assessment attempts allowed"
    )

    # Self-enrollment
    allow_self_enrollment = models.BooleanField(
        default=True,
        help_text="Employees can self-enroll"
    )

    # Related content
    prerequisite_courses = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='dependent_courses',
        help_text="Courses that must be completed first"
    )

    # Resources
    attachments = models.ManyToManyField(
        Document,
        blank=True,
        related_name='courses',
        help_text="Course materials and resources"
    )

    # Thumbnail/cover image
    cover_image = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_covers'
    )

    # Metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)
    average_completion_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average completion time in minutes"
    )

    # Published date
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Training Course'
        verbose_name_plural = 'Training Courses'
        ordering = ['-is_mandatory', 'course_type', 'title']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['course_type', 'status']),
            models.Index(fields=['is_mandatory']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['public_id']),
        ]
        permissions = [
            ('can_publish_course', 'Can publish training courses'),
            ('can_enroll_others', 'Can enroll other employees'),
        ]

    def __str__(self):
        return f"{self.code}: {self.title}"

    @property
    def duration_display(self):
        """Human-readable duration"""
        hours = self.estimated_duration_minutes // 60
        minutes = self.estimated_duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def completion_rate(self):
        """Percentage of enrollments that completed"""
        if self.total_enrollments > 0:
            return (self.total_completions / self.total_enrollments) * 100
        return 0

    @property
    def lesson_count(self):
        """Number of lessons in the course"""
        return self.lessons.filter(is_deleted=False).count()


class TrainingLesson(AuditMixin, SoftDeleteMixin, models.Model):
    """
    Individual lesson within a training course.
    Can reference existing knowledge articles for content reuse.
    """

    class LessonType(models.TextChoices):
        VIDEO = 'VIDEO', 'Video Lesson'
        READING = 'READING', 'Reading Material'
        INTERACTIVE = 'INTERACTIVE', 'Interactive Content'
        QUIZ = 'QUIZ', 'Quiz/Assessment'
        PRACTICAL = 'PRACTICAL', 'Practical Exercise'
        DISCUSSION = 'DISCUSSION', 'Discussion/Q&A'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    sequence = models.PositiveIntegerField(
        default=1,
        help_text="Order within the course"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.READING
    )

    # Content options
    # Option 1: Reference existing article (content reuse)
    linked_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_in_lessons',
        help_text="Link to knowledge article for content"
    )

    # Option 2: Direct content
    content = models.TextField(
        blank=True,
        help_text="Lesson content (if not using linked article)"
    )

    # Option 3: External video/link
    external_url = models.URLField(
        blank=True,
        help_text="External video or resource URL"
    )

    # Attachments
    attachments = models.ManyToManyField(
        Document,
        blank=True,
        related_name='lessons'
    )

    # Requirements
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Must complete to finish course"
    )
    min_time_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Minimum time to spend on lesson (0 = no minimum)"
    )

    # For quiz/assessment lessons
    questions = models.JSONField(
        null=True,
        blank=True,
        help_text="Quiz questions in JSON format"
    )
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text="Minimum passing score for quiz lessons"
    )

    # Estimated duration
    estimated_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Estimated time to complete this lesson"
    )

    class Meta:
        verbose_name = 'Training Lesson'
        verbose_name_plural = 'Training Lessons'
        ordering = ['course', 'sequence']
        indexes = [
            models.Index(fields=['course', 'sequence']),
        ]

    def __str__(self):
        return f"{self.course.code} - Lesson {self.sequence}: {self.title}"

    @property
    def content_to_display(self):
        """Get content from linked article or direct content"""
        if self.linked_article:
            return self.linked_article.body
        return self.content


class TrainingEnrollment(models.Model):
    """
    Employee enrollment in a training course.
    Tracks progress and completion status.
    """

    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        EXPIRED = 'EXPIRED', 'Expired'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='training_enrollments'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED
    )

    # Enrollment details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_enrollments_created'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When completion expires (for courses with validity_months)"
    )

    # Progress
    progress_percentage = models.FloatField(
        default=0,
        help_text="Overall completion percentage (0-100)"
    )
    lessons_completed = models.PositiveIntegerField(default=0)
    total_time_spent_minutes = models.PositiveIntegerField(default=0)

    # Assessment
    final_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Final assessment score (0-100)"
    )
    assessment_attempts = models.PositiveIntegerField(default=0)
    passed_assessment = models.BooleanField(default=False)

    # Certification
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this enrollment"
    )

    class Meta:
        verbose_name = 'Training Enrollment'
        verbose_name_plural = 'Training Enrollments'
        unique_together = [['course', 'employee']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['enrolled_at']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.course.code}"

    @property
    def is_expired(self):
        """Check if completion has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    @property
    def days_until_expiry(self):
        """Days until certification expires"""
        if self.expires_at:
            from django.utils import timezone
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return None

    def mark_completed(self, score=None):
        """Mark enrollment as completed and handle certification"""
        from django.utils import timezone

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.progress_percentage = 100.0

        if score is not None:
            self.final_score = score
            self.passed_assessment = score >= self.course.passing_score

        # Set expiry if course has validity period
        if self.course.validity_months:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(
                days=self.course.validity_months * 30
            )

        # Issue certificate
        if not self.course.requires_assessment or self.passed_assessment:
            self._issue_certificate()

        self.save()

        # Grant HR qualification if configured
        self._grant_qualification()

    def _issue_certificate(self):
        """Generate certificate number"""
        from django.utils import timezone
        import uuid

        self.certificate_issued = True
        self.certificate_number = f"CERT-{self.course.code}-{uuid.uuid4().hex[:8].upper()}"
        self.certificate_issued_at = timezone.now()

    def _grant_qualification(self):
        """Create HR qualification record if course grants one"""
        if not self.course.grants_qualification:
            return

        from floor_app.operations.hr.models import HREmployeeQualification

        # Check if qualification already exists
        existing = HREmployeeQualification.objects.filter(
            employee=self.employee,
            qualification=self.course.grants_qualification
        ).first()

        if existing:
            # Update expiry if exists
            if self.expires_at:
                existing.expires_at = self.expires_at
                existing.status = 'ACTIVE'
                existing.save()
        else:
            # Create new qualification
            HREmployeeQualification.objects.create(
                employee=self.employee,
                qualification=self.course.grants_qualification,
                issued_at=self.completed_at,
                expires_at=self.expires_at,
                status='ACTIVE',
                doc_ref=self.certificate_number,
                remarks=f"Granted from training: {self.course.title}"
            )


class TrainingLessonProgress(models.Model):
    """
    Track individual lesson completion within an enrollment.
    """
    enrollment = models.ForeignKey(
        TrainingEnrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey(
        TrainingLesson,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )

    # Status
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    # Time tracking
    time_spent_seconds = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    # For quiz lessons
    quiz_score = models.FloatField(null=True, blank=True)
    quiz_attempts = models.PositiveIntegerField(default=0)
    quiz_answers = models.JSONField(
        null=True,
        blank=True,
        help_text="User's quiz answers"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="User's notes for this lesson"
    )

    class Meta:
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = [['enrollment', 'lesson']]
        ordering = ['lesson__sequence']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
        ]

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.enrollment.employee} - {self.lesson.title} ({status})"

    def mark_completed(self):
        """Mark this lesson as completed"""
        from django.utils import timezone

        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

        # Update enrollment progress
        self._update_enrollment_progress()

    def _update_enrollment_progress(self):
        """Update the parent enrollment's progress"""
        enrollment = self.enrollment
        course = enrollment.course

        # Count completed mandatory lessons
        total_mandatory = course.lessons.filter(is_mandatory=True, is_deleted=False).count()
        completed_mandatory = enrollment.lesson_progress.filter(
            lesson__is_mandatory=True,
            is_completed=True
        ).count()

        if total_mandatory > 0:
            enrollment.progress_percentage = (completed_mandatory / total_mandatory) * 100
        enrollment.lessons_completed = enrollment.lesson_progress.filter(is_completed=True).count()

        # Auto-complete enrollment if all mandatory lessons done
        if completed_mandatory >= total_mandatory and not course.requires_assessment:
            enrollment.mark_completed()
        else:
            enrollment.save()


class TrainingSchedule(AuditMixin, SoftDeleteMixin, models.Model):
    """
    Scheduled training sessions (for instructor-led or live trainings).
    """
    course = models.ForeignKey(
        TrainingCourse,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    title = models.CharField(
        max_length=255,
        help_text="Session title (e.g., 'Safety Training - March 2025')"
    )
    description = models.TextField(blank=True)

    # Timing
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone_name = models.CharField(
        max_length=50,
        default='Asia/Riyadh'
    )

    # Location
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical location or 'Online'"
    )
    meeting_link = models.URLField(
        blank=True,
        help_text="Online meeting URL"
    )

    # Capacity
    max_participants = models.PositiveIntegerField(
        default=20,
        help_text="Maximum number of participants"
    )
    min_participants = models.PositiveIntegerField(
        default=1,
        help_text="Minimum participants to run session"
    )

    # Instructor
    instructor = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_sessions_conducted'
    )
    external_instructor = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of external instructor if applicable"
    )

    # Registration
    registration_open = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Training Schedule'
        verbose_name_plural = 'Training Schedules'
        ordering = ['scheduled_date', 'start_time']
        indexes = [
            models.Index(fields=['course', 'scheduled_date']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.scheduled_date}"

    @property
    def registered_count(self):
        """Number of registered participants"""
        return self.registrations.count()

    @property
    def available_spots(self):
        """Available spots remaining"""
        return max(0, self.max_participants - self.registered_count)

    @property
    def is_full(self):
        """Check if session is at capacity"""
        return self.registered_count >= self.max_participants


class TrainingScheduleRegistration(models.Model):
    """
    Employee registration for a scheduled training session.
    """

    class AttendanceStatus(models.TextChoices):
        REGISTERED = 'REGISTERED', 'Registered'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        ATTENDED = 'ATTENDED', 'Attended'
        ABSENT = 'ABSENT', 'Absent'
        CANCELLED = 'CANCELLED', 'Cancelled'

    schedule = models.ForeignKey(
        TrainingSchedule,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='training_registrations'
    )

    registered_at = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.REGISTERED
    )
    attendance_marked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Schedule Registration'
        verbose_name_plural = 'Schedule Registrations'
        unique_together = [['schedule', 'employee']]

    def __str__(self):
        return f"{self.employee} - {self.schedule}"

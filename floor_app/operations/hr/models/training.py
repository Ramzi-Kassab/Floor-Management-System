"""
Training and Development Models

Tracks employee training, certifications, and professional development.
"""

from django.db import models
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class TrainingType:
    """Types of training"""
    ONBOARDING = 'ONBOARDING'
    TECHNICAL = 'TECHNICAL'
    SAFETY = 'SAFETY'
    COMPLIANCE = 'COMPLIANCE'
    SOFT_SKILLS = 'SOFT_SKILLS'
    LEADERSHIP = 'LEADERSHIP'
    CERTIFICATION = 'CERTIFICATION'
    EXTERNAL = 'EXTERNAL'

    CHOICES = [
        (ONBOARDING, 'Onboarding/Induction'),
        (TECHNICAL, 'Technical Training'),
        (SAFETY, 'Health & Safety'),
        (COMPLIANCE, 'Compliance & Regulatory'),
        (SOFT_SKILLS, 'Soft Skills'),
        (LEADERSHIP, 'Leadership & Management'),
        (CERTIFICATION, 'Professional Certification'),
        (EXTERNAL, 'External Training'),
    ]


class TrainingStatus:
    """Training status"""
    SCHEDULED = 'SCHEDULED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'

    CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (FAILED, 'Failed/Did Not Complete'),
    ]


class TrainingProgram(AuditMixin, SoftDeleteMixin):
    """
    Training program/course definition.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    training_type = models.CharField(
        max_length=20,
        choices=TrainingType.CHOICES,
        db_index=True
    )
    description = models.TextField(blank=True)

    # Duration
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total duration in hours"
    )
    duration_days = models.IntegerField(
        default=1,
        help_text="Duration in days"
    )

    # Provider
    provider = models.CharField(
        max_length=200,
        blank=True,
        help_text="Training provider/instructor"
    )
    is_internal = models.BooleanField(
        default=True,
        help_text="Internal or external training"
    )

    # Requirements
    prerequisites = models.TextField(
        blank=True,
        help_text="Prerequisites for this training"
    )
    target_audience = models.TextField(
        blank=True,
        help_text="Target audience/positions"
    )
    max_participants = models.IntegerField(default=20)

    # Assessment
    has_assessment = models.BooleanField(default=False)
    passing_score = models.IntegerField(
        default=70,
        help_text="Minimum passing score percentage"
    )

    # Certification
    grants_certificate = models.BooleanField(default=False)
    certificate_validity_months = models.IntegerField(
        default=0,
        help_text="Months before certificate expires (0 = no expiry)"
    )

    # Cost
    cost_per_person = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='SAR')

    # Compliance
    is_mandatory = models.BooleanField(
        default=False,
        help_text="Mandatory for certain positions"
    )
    mandatory_for_positions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of position IDs this is mandatory for"
    )

    is_active = models.BooleanField(default=True)
    materials_path = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'hr_training_program'
        verbose_name = 'Training Program'
        verbose_name_plural = 'Training Programs'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class TrainingSession(AuditMixin, SoftDeleteMixin):
    """
    Specific training session/event.
    """
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    session_code = models.CharField(max_length=30, unique=True)
    status = models.CharField(
        max_length=15,
        choices=TrainingStatus.CHOICES,
        default=TrainingStatus.SCHEDULED,
        db_index=True
    )

    # Schedule
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    # Location
    location = models.CharField(max_length=200)
    is_virtual = models.BooleanField(default=False)
    virtual_link = models.URLField(blank=True)

    # Instructor
    instructor_name = models.CharField(max_length=200)
    instructor_contact = models.CharField(max_length=100, blank=True)

    # Participants
    registered_count = models.IntegerField(default=0)
    attended_count = models.IntegerField(default=0)
    passed_count = models.IntegerField(default=0)

    # Materials
    materials_distributed = models.BooleanField(default=False)

    notes = models.TextField(blank=True)
    feedback_summary = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_training_session'
        verbose_name = 'Training Session'
        verbose_name_plural = 'Training Sessions'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.session_code} - {self.program.name}"

    @classmethod
    def generate_session_code(cls, program):
        """Generate session code"""
        year = timezone.now().year
        prefix = f'{program.code}-{year}-'
        last_session = cls.all_objects.filter(
            session_code__startswith=prefix
        ).order_by('-session_code').first()

        if last_session:
            last_num = int(last_session.session_code.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:03d}"


class EmployeeTraining(AuditMixin):
    """
    Employee's training record.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='training_records'
    )
    training_session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='participants'
    )

    # Registration
    registered_at = models.DateTimeField(default=timezone.now)
    registered_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Registered by (manager/HR)"
    )

    # Attendance
    attended = models.BooleanField(default=False)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of sessions attended"
    )

    # Assessment
    assessment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Assessment score percentage"
    )
    passed = models.BooleanField(default=False)
    attempts = models.IntegerField(default=1)

    # Certificate
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_issued_date = models.DateField(null=True, blank=True)
    certificate_expiry_date = models.DateField(null=True, blank=True)
    certificate_path = models.CharField(max_length=500, blank=True)

    # Feedback
    feedback_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )
    feedback_comments = models.TextField(blank=True)

    # Cost
    cost_incurred = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Status
    completion_status = models.CharField(
        max_length=15,
        choices=TrainingStatus.CHOICES,
        default=TrainingStatus.SCHEDULED
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_employee_training'
        verbose_name = 'Employee Training'
        verbose_name_plural = 'Employee Training Records'
        unique_together = [['employee', 'training_session']]
        ordering = ['-training_session__start_date']

    def __str__(self):
        return f"{self.employee.employee_no} - {self.training_session.session_code}"

    def mark_completed(self, passed=True, score=None):
        """Mark training as completed"""
        self.completion_status = TrainingStatus.COMPLETED
        self.completed_at = timezone.now()
        self.passed = passed
        if score is not None:
            self.assessment_score = score

        # Issue certificate if applicable
        if passed and self.training_session.program.grants_certificate:
            self.certificate_issued_date = timezone.now().date()
            if self.training_session.program.certificate_validity_months > 0:
                from datetime import timedelta
                self.certificate_expiry_date = (
                    timezone.now().date() +
                    timedelta(days=self.training_session.program.certificate_validity_months * 30)
                )
            self.certificate_number = f"CERT-{self.employee.employee_no}-{self.training_session.session_code}"

        self.save()


class SkillMatrix(AuditMixin):
    """
    Employee skill matrix for competency tracking.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='skills'
    )

    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(
        max_length=50,
        default='TECHNICAL',
        choices=[
            ('TECHNICAL', 'Technical'),
            ('SOFTWARE', 'Software/Tools'),
            ('LANGUAGE', 'Language'),
            ('CERTIFICATION', 'Certification'),
            ('SOFT_SKILL', 'Soft Skill'),
            ('DOMAIN', 'Domain Knowledge'),
        ]
    )

    # Proficiency Level
    proficiency_level = models.CharField(
        max_length=20,
        default='BEGINNER',
        choices=[
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert'),
        ]
    )
    proficiency_score = models.IntegerField(
        default=1,
        help_text="Score 1-5"
    )

    # Experience
    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0
    )

    # Verification
    verified = models.BooleanField(default=False)
    verified_by_id = models.BigIntegerField(null=True, blank=True)
    verification_date = models.DateField(null=True, blank=True)
    verification_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Assessment, certification, manager review, etc."
    )

    # Training Link
    related_training = models.ForeignKey(
        EmployeeTraining,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skills_gained'
    )

    last_used_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_skill_matrix'
        verbose_name = 'Skill Entry'
        verbose_name_plural = 'Skill Matrix'
        unique_together = [['employee', 'skill_name']]
        ordering = ['employee', 'skill_category', 'skill_name']

    def __str__(self):
        return f"{self.employee.employee_no} - {self.skill_name} ({self.get_proficiency_level_display()})"

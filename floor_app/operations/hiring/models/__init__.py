"""Hiring/Recruitment Portal Models"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin


class JobPosting(AuditMixin):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
    )

    job_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=(
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Internship'),
    ))
    experience_level = models.CharField(max_length=20, choices=(
        ('ENTRY', 'Entry Level'),
        ('MID', 'Mid Level'),
        ('SENIOR', 'Senior Level'),
        ('EXECUTIVE', 'Executive'),
    ))

    # Details
    description = models.TextField()
    responsibilities = models.TextField()
    requirements = models.TextField()
    preferred_qualifications = models.TextField(blank=True)

    # Compensation
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    benefits = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='jobs_posted')
    posted_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    positions_count = models.IntegerField(default=1)
    positions_filled = models.IntegerField(default=0)

    # Hiring Team
    hiring_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_jobs')
    recruiters = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='recruited_jobs')

    class Meta:
        db_table = 'job_postings'
        ordering = ['-posted_date']

    def __str__(self):
        return f"{self.job_code} - {self.title}"


class Candidate(AuditMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    current_location = models.CharField(max_length=200, blank=True)
    linkedin_profile = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Experience
    current_company = models.CharField(max_length=200, blank=True)
    current_position = models.CharField(max_length=200, blank=True)
    total_experience_years = models.IntegerField(null=True, blank=True)

    # Education
    highest_education = models.CharField(max_length=100, blank=True)
    university = models.CharField(max_length=200, blank=True)

    # Documents
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    cover_letter = models.FileField(upload_to='cover_letters/', null=True, blank=True)

    # Status
    is_blacklisted = models.BooleanField(default=False)
    blacklist_reason = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'candidates'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class JobApplication(AuditMixin):
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('SCREENING', 'Under Screening'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interview Scheduled'),
        ('OFFER', 'Offer Extended'),
        ('ACCEPTED', 'Offer Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    application_number = models.CharField(max_length=50, unique=True)
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')

    # Application Details
    applied_date = models.DateTimeField(auto_now_add=True)
    cover_letter_text = models.TextField(blank=True)
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    available_from = models.DateField(null=True, blank=True)
    notice_period_days = models.IntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_applications')

    # Evaluation
    screening_score = models.IntegerField(null=True, blank=True)
    screening_notes = models.TextField(blank=True)
    overall_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    # Rejection
    rejection_reason = models.TextField(blank=True)
    rejection_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'job_applications'
        unique_together = [['job_posting', 'candidate']]
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.application_number} - {self.candidate}"


class Interview(AuditMixin):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'),
        ('NO_SHOW', 'No Show'),
    )

    INTERVIEW_TYPES = (
        ('PHONE', 'Phone Screening'),
        ('VIDEO', 'Video Interview'),
        ('IN_PERSON', 'In-Person'),
        ('TECHNICAL', 'Technical Round'),
        ('HR', 'HR Interview'),
        ('FINAL', 'Final Round'),
    )

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    round_number = models.IntegerField(default=1)

    # Schedule
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True)

    # Interviewers
    interviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='interviews_conducted')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    # Feedback
    feedback = models.TextField(blank=True)
    technical_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    cultural_fit_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_recommendation = models.CharField(max_length=20, choices=(
        ('STRONG_YES', 'Strong Yes'),
        ('YES', 'Yes'),
        ('MAYBE', 'Maybe'),
        ('NO', 'No'),
        ('STRONG_NO', 'Strong No'),
    ), blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'interviews'
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"{self.application.candidate} - {self.get_interview_type_display()}"


class JobOffer(AuditMixin):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Candidate'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('NEGOTIATING', 'Under Negotiation'),
        ('EXPIRED', 'Expired'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    offer_number = models.CharField(max_length=50, unique=True)
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='offers')

    # Offer Details
    position_title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    reporting_to = models.CharField(max_length=200)
    start_date = models.DateField()

    # Compensation
    annual_salary = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    bonus = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    benefits = models.TextField()

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    sent_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    response_date = models.DateField(null=True, blank=True)

    # Documents
    offer_letter = models.FileField(upload_to='offer_letters/', null=True, blank=True)

    # Approval
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_offers')
    approval_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'job_offers'
        ordering = ['-sent_date']

    def __str__(self):
        return f"{self.offer_number} - {self.application.candidate}"

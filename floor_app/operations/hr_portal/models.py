"""
HR Portal Models

Models for employee self-service portal functionality.
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class EmployeeRequest(models.Model):
    """
    Generic employee request model.

    Tracks various types of employee requests submitted through the portal
    (e.g., document requests, information updates, certificate requests).
    """

    REQUEST_TYPE_CHOICES = [
        ('certificate', 'Employment Certificate'),
        ('salary_certificate', 'Salary Certificate'),
        ('document_copy', 'Document Copy'),
        ('info_update', 'Personal Information Update'),
        ('leave_balance', 'Leave Balance Inquiry'),
        ('other', 'Other Request'),
    ]

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Request identification
    request_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique request number'
    )

    # Employee who submitted the request
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='portal_requests',
        help_text='Employee who submitted this request'
    )

    # Request details
    request_type = models.CharField(
        max_length=30,
        choices=REQUEST_TYPE_CHOICES,
        help_text='Type of request'
    )

    subject = models.CharField(
        max_length=200,
        help_text='Request subject'
    )

    description = models.TextField(
        help_text='Detailed description of the request'
    )

    # Priority and status
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text='Request priority'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        help_text='Current status'
    )

    # Attachments
    attachment = models.FileField(
        upload_to='hr_portal/requests/',
        null=True,
        blank=True,
        help_text='Supporting document or file'
    )

    # Related object (generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Type of related object'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of related object'
    )
    related_object = GenericForeignKey('content_type', 'object_id')

    # Response
    response = models.TextField(
        blank=True,
        help_text='Response from HR'
    )

    response_attachment = models.FileField(
        upload_to='hr_portal/responses/',
        null=True,
        blank=True,
        help_text='Response document (e.g., issued certificate)'
    )

    # Workflow
    submitted_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date request was submitted'
    )

    reviewed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date request was reviewed'
    )

    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date request was completed'
    )

    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_employee_requests',
        help_text='HR user who reviewed this request'
    )

    # Audit
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hr_employee_request'
        verbose_name = 'Employee Request'
        verbose_name_plural = 'Employee Requests'
        ordering = ['-submitted_date']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['request_type']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_date']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.get_request_type_display()} ({self.employee.employee_code})"

    @property
    def is_pending(self):
        """Check if request is still pending."""
        return self.status in ['submitted', 'under_review']

    @property
    def is_closed(self):
        """Check if request is closed."""
        return self.status in ['approved', 'rejected', 'completed', 'cancelled']

    def save(self, *args, **kwargs):
        # Auto-generate request number if not provided
        if not self.request_number:
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = EmployeeRequest.objects.filter(
                request_number__startswith=f'REQ-{year}{month:02d}'
            ).count() + 1
            self.request_number = f'REQ-{year}{month:02d}-{count:04d}'

        super().save(*args, **kwargs)

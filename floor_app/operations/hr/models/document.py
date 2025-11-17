"""
Employee Document Management Models

Manages employee documents including contracts, certificates, IDs, and compliance documents.
"""

from django.db import models
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class DocumentType:
    """Types of employee documents"""
    CONTRACT = 'CONTRACT'
    ID_DOCUMENT = 'ID_DOCUMENT'
    PASSPORT = 'PASSPORT'
    VISA = 'VISA'
    WORK_PERMIT = 'WORK_PERMIT'
    CERTIFICATE = 'CERTIFICATE'
    QUALIFICATION = 'QUALIFICATION'
    MEDICAL = 'MEDICAL'
    INSURANCE = 'INSURANCE'
    PERFORMANCE = 'PERFORMANCE'
    LETTER = 'LETTER'
    OTHER = 'OTHER'

    CHOICES = [
        (CONTRACT, 'Employment Contract'),
        (ID_DOCUMENT, 'ID Document (Iqama/National ID)'),
        (PASSPORT, 'Passport'),
        (VISA, 'Visa'),
        (WORK_PERMIT, 'Work Permit'),
        (CERTIFICATE, 'Professional Certificate'),
        (QUALIFICATION, 'Educational Qualification'),
        (MEDICAL, 'Medical Certificate/Report'),
        (INSURANCE, 'Insurance Document'),
        (PERFORMANCE, 'Performance Review'),
        (LETTER, 'Official Letter'),
        (OTHER, 'Other Document'),
    ]


class DocumentStatus:
    """Document status"""
    VALID = 'VALID'
    EXPIRED = 'EXPIRED'
    EXPIRING_SOON = 'EXPIRING_SOON'
    PENDING_RENEWAL = 'PENDING_RENEWAL'
    ARCHIVED = 'ARCHIVED'

    CHOICES = [
        (VALID, 'Valid'),
        (EXPIRED, 'Expired'),
        (EXPIRING_SOON, 'Expiring Soon'),
        (PENDING_RENEWAL, 'Pending Renewal'),
        (ARCHIVED, 'Archived'),
    ]


class EmployeeDocument(AuditMixin, SoftDeleteMixin):
    """
    Employee document record.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='documents'
    )

    # Document Details
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.CHOICES,
        db_index=True
    )
    title = models.CharField(max_length=200)
    document_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Document number/reference"
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.CHOICES,
        default=DocumentStatus.VALID,
        db_index=True
    )

    # Dates
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expiry date (if applicable)"
    )
    renewal_reminder_days = models.IntegerField(
        default=30,
        help_text="Days before expiry to send reminder"
    )

    # Issuing Authority
    issuing_authority = models.CharField(max_length=200, blank=True)
    issuing_country = models.CharField(max_length=100, blank=True)

    # File Storage
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to uploaded document"
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by_id = models.BigIntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    # Confidentiality
    is_confidential = models.BooleanField(default=False)
    access_restricted = models.BooleanField(
        default=False,
        help_text="Restrict access to HR only"
    )

    # Compliance
    is_mandatory = models.BooleanField(
        default=False,
        help_text="Mandatory document for employment"
    )
    compliance_category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Compliance category (Saudi Labor Law, etc.)"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_employee_document'
        verbose_name = 'Employee Document'
        verbose_name_plural = 'Employee Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'document_type'], name='ix_doc_emp_type'),
            models.Index(fields=['expiry_date'], name='ix_doc_expiry'),
        ]

    def __str__(self):
        return f"{self.employee.employee_no} - {self.title}"

    def check_expiry_status(self):
        """Update status based on expiry date"""
        if not self.expiry_date:
            return

        today = timezone.now().date()
        days_to_expiry = (self.expiry_date - today).days

        if days_to_expiry < 0:
            self.status = DocumentStatus.EXPIRED
        elif days_to_expiry <= self.renewal_reminder_days:
            self.status = DocumentStatus.EXPIRING_SOON
        else:
            self.status = DocumentStatus.VALID

        self.save(update_fields=['status'])

    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days

    @property
    def is_expired(self):
        """Check if document is expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()


class DocumentRenewal(AuditMixin):
    """
    Track document renewal requests and history.
    """
    document = models.ForeignKey(
        EmployeeDocument,
        on_delete=models.CASCADE,
        related_name='renewals'
    )

    # Renewal Details
    request_date = models.DateField(default=timezone.now)
    new_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="New expiry date after renewal"
    )

    # Status
    status = models.CharField(
        max_length=20,
        default='REQUESTED',
        choices=[
            ('REQUESTED', 'Requested'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
        ]
    )

    # Costs
    renewal_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    paid_by = models.CharField(
        max_length=20,
        default='COMPANY',
        choices=[
            ('COMPANY', 'Company'),
            ('EMPLOYEE', 'Employee'),
            ('SHARED', 'Shared'),
        ]
    )

    # New Document
    new_document_number = models.CharField(max_length=100, blank=True)
    new_file_path = models.CharField(max_length=500, blank=True)

    # Processing
    processed_by_id = models.BigIntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_document_renewal'
        verbose_name = 'Document Renewal'
        verbose_name_plural = 'Document Renewals'
        ordering = ['-request_date']

    def __str__(self):
        return f"Renewal: {self.document.title} ({self.status})"

    def complete_renewal(self, new_expiry_date=None):
        """Mark renewal as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if new_expiry_date:
            self.new_expiry_date = new_expiry_date

            # Update original document
            self.document.expiry_date = new_expiry_date
            self.document.status = DocumentStatus.VALID
            self.document.save(update_fields=['expiry_date', 'status'])

        self.save()


class ExpiryAlert(AuditMixin):
    """
    Alert for document expiry notification tracking.
    """
    document = models.ForeignKey(
        EmployeeDocument,
        on_delete=models.CASCADE,
        related_name='expiry_alerts'
    )

    alert_date = models.DateField(default=timezone.now)
    days_before_expiry = models.IntegerField()

    # Notification
    notified_employee = models.BooleanField(default=False)
    employee_notified_at = models.DateTimeField(null=True, blank=True)

    notified_hr = models.BooleanField(default=False)
    hr_notified_at = models.DateTimeField(null=True, blank=True)

    notified_manager = models.BooleanField(default=False)
    manager_notified_at = models.DateTimeField(null=True, blank=True)

    # Action
    action_taken = models.TextField(blank=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by_id = models.BigIntegerField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hr_expiry_alert'
        verbose_name = 'Expiry Alert'
        verbose_name_plural = 'Expiry Alerts'
        ordering = ['-alert_date']

    def __str__(self):
        return f"Alert: {self.document.title} expires in {self.days_before_expiry} days"

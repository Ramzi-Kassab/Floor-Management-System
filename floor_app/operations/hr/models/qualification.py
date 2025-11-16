from django.db import models

from floor_app.mixins import HRAuditMixin, HRSoftDeleteMixin


class HRQualification(HRAuditMixin, HRSoftDeleteMixin):
    ISSUER_TYPE = (
        ("INTERNAL", "Internal"),
        ("EXTERNAL", "External"),
    )

    code = models.CharField(max_length=64, unique=True)   # e.g. BRAZING_L1
    name = models.CharField(max_length=120)

    level = models.PositiveSmallIntegerField(null=True, blank=True)

    issuer_type = models.CharField(
        max_length=16, choices=ISSUER_TYPE, default="INTERNAL"
    )
    validity_months = models.PositiveSmallIntegerField(null=True, blank=True)
    requires_renewal = models.BooleanField(default=True)

    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hr_qualification"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

class HREmployeeQualification(HRAuditMixin, HRSoftDeleteMixin):
    STATUS = (
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("SUSPENDED", "Suspended"),
        ("PENDING", "Pending"),
    )

    employee = models.ForeignKey(
        "HREmployee",
        on_delete=models.PROTECT,
        related_name="qualifications",
    )

    qualification = models.ForeignKey(
        "HRQualification",
        on_delete=models.PROTECT,
        related_name="employee_links",
    )

    issued_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=16, choices=STATUS, default="ACTIVE")

    doc_ref = models.CharField(max_length=255, blank=True, default="")   # certificate file ref / code
    remarks = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "hr_employee_qualification"
        # You can later add a constraint to prevent multiple ACTIVE rows for same (employee, qualification)
        indexes = [
            models.Index(fields=["employee", "qualification", "status"]),
        ]

    def __str__(self):
        return f"{self.employee} / {self.qualification} ({self.status})"

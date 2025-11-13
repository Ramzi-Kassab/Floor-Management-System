from django.conf import settings
from django.db import models

from ..mixins import HRAuditMixin, HRSoftDeleteMixin
from ...mixins import PublicIdMixin  # from floor_app.mixins


class HREmployee(PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin):
    STATUS = (
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On leave"),
        ("SUSPENDED", "Suspended"),
        ("TERMINATED", "Terminated"),
    )

    person = models.OneToOneField(
        "HRPeople",
        on_delete=models.PROTECT,
        related_name="employee",
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_employee",
    )

    employee_no = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=16, choices=STATUS, default="ACTIVE")

    job_title = models.CharField(max_length=120, blank=True, default="")
    team = models.CharField(max_length=64, blank=True, default="")        # e.g. PDC_BRAZING, QC, LOGISTICS
    is_operator = models.BooleanField(default=True)                       # can be assigned to floor ops

    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "hr_employee"
        ordering = ["employee_no"]

    def __str__(self):
        base = f"{self.employee_no}"
        if self.person_id:
            return f"{base} - {self.person}"
        return base

    @property
    def phones(self):
        return self.person.phones.all()

    @property
    def emails(self):
        return self.person.emails.all()

    @property
    def addresses(self):
        return self.person.addresses.all()
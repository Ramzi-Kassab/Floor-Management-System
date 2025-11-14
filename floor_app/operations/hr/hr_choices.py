from django.db import models


class HRRateType(models.TextChoices):
    SALARY = "SALARY", "Salary"
    HOURLY = "HOURLY", "Hourly"


class HRLeaveType(models.TextChoices):
    ANNUAL = "ANNUAL", "Annual"
    SICK = "SICK", "Sick"
    PERSONAL = "PERSONAL", "Personal"
    UNPAID = "UNPAID", "Unpaid"


class HRRequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    DENIED = "DENIED", "Denied"
    CANCELLED = "CANCELLED", "Cancelled"


class HRApplicationStage(models.TextChoices):
    APPLIED = "APPLIED", "Applied"
    SCREEN = "SCREEN", "Screening"
    INTERVIEW = "INTERVIEW", "Interview"
    OFFER = "OFFER", "Offer"
    HIRED = "HIRED", "Hired"
    REJECTED = "REJECTED", "Rejected"


class HRDocumentType(models.TextChoices):
    PASSPORT = "PASSPORT", "Passport"
    NATIONAL_ID = "NATIONAL_ID", "National ID"
    RESIDENCY = "RESIDENCY", "Residency Permit"
    INSURANCE = "INSURANCE", "Insurance Card"
    VISA = "VISA", "Visa"

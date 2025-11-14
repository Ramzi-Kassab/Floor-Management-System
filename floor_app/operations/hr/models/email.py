from django.db import models
from django.core.validators import EmailValidator
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError

from floor_app.mixins import HRAuditMixin, HRSoftDeleteMixin

# Optional: pypi.org/project/email-validator (more robust RFC/IDN validation)
try:
    from email_validator import validate_email as _ev_validate, EmailNotValidError  # type: ignore
    _HAS_EMAIL_VALIDATOR = True
except Exception:  # pragma: no cover
    _HAS_EMAIL_VALIDATOR = False


class HREmail(HRAuditMixin, HRSoftDeleteMixin):
    """
    Canonical email record.
    - `email` is normalized to lowercase.
    - Case-insensitive uniqueness enforced (no duplicates).
    - `is_verified` allows a future verification workflow.
    """
    email = models.EmailField(max_length=254, db_index=True)
    KIND = (("PERSONAL", "Personal"), ("BUSINESS", "Business"))
    kind = models.CharField(max_length=8, choices=KIND, default="BUSINESS")

    is_primary_hint = models.BooleanField(default=False)
    label = models.CharField(max_length=64, blank=True, default="")

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    person = models.ForeignKey(
        "HRPeople",
        on_delete=models.PROTECT,
        related_name="emails",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "hr_email"
        constraints = [
            # prevent duplicates regardless of case
            models.UniqueConstraint(Lower("email"), name="uq_hr_email_ci"),
        ]

    def clean(self):
        if not self.email:
            raise ValidationError("Email is required.")

        # normalize casing/whitespace
        self.email = self.email.strip().lower()

        if _HAS_EMAIL_VALIDATOR:
            # robust RFC & IDN rules; validates domain (MX/A/AAAA) as well
            try:
                info = _ev_validate(self.email, check_deliverability=True)
                # Use normalized form (punycode/idna handled)
                self.email = info.normalized.lower()
            except EmailNotValidError as e:
                raise ValidationError(str(e))
        else:
            # fallback to Django's built-in validator
            EmailValidator()(self.email)

    def __str__(self):
        return self.email

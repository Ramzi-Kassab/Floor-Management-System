"""
Custom validators and mixins for Floor Management System

Provides:
- Custom field validators
- Model mixins
- Validation utilities
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta
import re


# ============================================================================
# FIELD VALIDATORS
# ============================================================================

def validate_phone_number(value):
    """
    Validate phone number format
    Accepts: +1234567890, (123) 456-7890, 123-456-7890, etc.
    """
    if not value:
        return

    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', value)

    # Check if it's all digits
    if not cleaned.isdigit():
        raise ValidationError(
            _('Phone number must contain only digits and formatting characters (+, -, (), spaces).')
        )

    # Check length (7-15 digits is reasonable for international numbers)
    if len(cleaned) < 7 or len(cleaned) > 15:
        raise ValidationError(
            _('Phone number must be between 7 and 15 digits.')
        )


def validate_email_domain(value, allowed_domains=None):
    """
    Validate that email is from allowed domains

    Usage:
        validators=[lambda v: validate_email_domain(v, ['company.com', 'partner.com'])]
    """
    if not value:
        return

    if allowed_domains:
        domain = value.split('@')[-1].lower()
        if domain not in allowed_domains:
            raise ValidationError(
                _('Email must be from one of these domains: %(domains)s'),
                params={'domains': ', '.join(allowed_domains)}
            )


def validate_future_date(value):
    """
    Validate that date is in the future
    """
    if value and value <= date.today():
        raise ValidationError(_('Date must be in the future.'))


def validate_past_date(value):
    """
    Validate that date is in the past
    """
    if value and value >= date.today():
        raise ValidationError(_('Date must be in the past.'))


def validate_not_weekend(value):
    """
    Validate that date is not a weekend
    """
    if value and value.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        raise ValidationError(_('Date cannot be on a weekend.'))


def validate_business_hours(value):
    """
    Validate that time is within business hours (8 AM - 6 PM)
    """
    from datetime import time
    if value:
        business_start = time(8, 0)
        business_end = time(18, 0)
        if not (business_start <= value <= business_end):
            raise ValidationError(
                _('Time must be within business hours (8:00 AM - 6:00 PM).')
            )


def validate_file_size(value, max_size_mb=5):
    """
    Validate file upload size

    Usage:
        validators=[lambda v: validate_file_size(v, max_size_mb=10)]
    """
    if value:
        if value.size > max_size_mb * 1024 * 1024:
            raise ValidationError(
                _('File size must not exceed %(max_size)s MB.'),
                params={'max_size': max_size_mb}
            )


def validate_image_dimensions(value, min_width=None, min_height=None,
                              max_width=None, max_height=None):
    """
    Validate image dimensions

    Usage:
        validators=[lambda v: validate_image_dimensions(v, min_width=800, min_height=600)]
    """
    if value:
        from PIL import Image
        img = Image.open(value)
        width, height = img.size

        if min_width and width < min_width:
            raise ValidationError(
                _('Image width must be at least %(width)s pixels.'),
                params={'width': min_width}
            )

        if min_height and height < min_height:
            raise ValidationError(
                _('Image height must be at least %(height)s pixels.'),
                params={'height': min_height}
            )

        if max_width and width > max_width:
            raise ValidationError(
                _('Image width must not exceed %(width)s pixels.'),
                params={'width': max_width}
            )

        if max_height and height > max_height:
            raise ValidationError(
                _('Image height must not exceed %(height)s pixels.'),
                params={'height': max_height}
            )


def validate_positive_decimal(value):
    """
    Validate that decimal is positive
    """
    if value and value <= 0:
        raise ValidationError(_('Value must be positive.'))


def validate_percentage(value):
    """
    Validate that value is between 0 and 100
    """
    if value is not None and (value < 0 or value > 100):
        raise ValidationError(_('Value must be between 0 and 100.'))


def validate_employee_code(value):
    """
    Validate employee code format: EMP + 6 digits
    """
    if not value:
        return

    pattern = r'^EMP\d{6}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Employee code must be in format: EMP followed by 6 digits (e.g., EMP000001).')
        )


def validate_asset_code(value):
    """
    Validate asset code format: AST + 6 digits
    """
    if not value:
        return

    pattern = r'^AST\d{6}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Asset code must be in format: AST followed by 6 digits (e.g., AST000001).')
        )


def validate_date_range(start_date, end_date, min_days=None, max_days=None):
    """
    Validate date range

    Usage in model's clean():
        validate_date_range(self.start_date, self.end_date, min_days=1, max_days=30)
    """
    if start_date and end_date:
        # End date must be after start date
        if end_date < start_date:
            raise ValidationError(_('End date must be after start date.'))

        # Check duration if specified
        duration = (end_date - start_date).days

        if min_days and duration < min_days:
            raise ValidationError(
                _('Date range must be at least %(days)s day(s).'),
                params={'days': min_days}
            )

        if max_days and duration > max_days:
            raise ValidationError(
                _('Date range must not exceed %(days)s day(s).'),
                params={'days': max_days}
            )


# ============================================================================
# REGEX VALIDATORS
# ============================================================================

# Alphanumeric with spaces and common punctuation
alphanumeric_validator = RegexValidator(
    r'^[a-zA-Z0-9\s\-\_\.]+$',
    _('Only alphanumeric characters, spaces, hyphens, underscores, and periods are allowed.')
)

# Only letters and spaces (for names)
name_validator = RegexValidator(
    r'^[a-zA-Z\s\-\']+$',
    _('Only letters, spaces, hyphens, and apostrophes are allowed.')
)

# Code format (uppercase letters and numbers)
code_validator = RegexValidator(
    r'^[A-Z0-9\-\_]+$',
    _('Only uppercase letters, numbers, hyphens, and underscores are allowed.')
)


# ============================================================================
# MODEL MIXINS
# ============================================================================

class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to models

    Usage:
        class MyModel(SoftDeleteMixin, models.Model):
            # your fields...
            pass

    Note: Add these fields to your model:
        is_deleted = models.BooleanField(default=False)
        deleted_at = models.DateTimeField(null=True, blank=True)
        deleted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    """

    def soft_delete(self, user=None):
        """Soft delete the object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @classmethod
    def get_active(cls):
        """Get only non-deleted objects"""
        return cls.objects.filter(is_deleted=False)


class AuditMixin:
    """
    Mixin to automatically track who created/updated records

    Note: Add these fields to your model:
        created_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.SET_NULL)
        updated_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.SET_NULL)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
    """

    def save_with_user(self, user, *args, **kwargs):
        """Save with user tracking"""
        if not self.pk:  # New record
            self.created_by = user
        self.updated_by = user
        self.save(*args, **kwargs)


class ValidateModelMixin:
    """
    Mixin to automatically call full_clean() before save

    Usage:
        class MyModel(ValidateModelMixin, models.Model):
            # your fields...
            pass
    """

    def save(self, *args, **kwargs):
        """Override save to call full_clean()"""
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)


class CodeGeneratorMixin:
    """
    Mixin to automatically generate unique codes

    Usage:
        class MyModel(CodeGeneratorMixin, models.Model):
            code = models.CharField(max_length=20, unique=True)

            code_prefix = 'EMP'
            code_length = 6

    Note: Set code_prefix and code_length as class attributes
    """

    code_prefix = 'CODE'
    code_length = 6

    def generate_code(self):
        """Generate a unique code"""
        import random

        max_attempts = 100
        for _ in range(max_attempts):
            # Generate random number
            number = ''.join([str(random.randint(0, 9)) for _ in range(self.code_length)])
            code = f"{self.code_prefix}{number}"

            # Check if code exists
            if not self.__class__.objects.filter(code=code).exists():
                return code

        # If we couldn't generate a unique code, use timestamp
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"{self.code_prefix}{timestamp}"

    def save(self, *args, **kwargs):
        """Auto-generate code if not provided"""
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_no_overlap(queryset, start_date, end_date, exclude_pk=None):
    """
    Validate that date range doesn't overlap with existing records

    Usage in model's clean():
        validate_no_overlap(
            queryset=ShiftAssignment.objects.filter(employee=self.employee),
            start_date=self.start_date,
            end_date=self.end_date,
            exclude_pk=self.pk
        )
    """
    from django.db.models import Q

    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)

    # Check for overlaps
    overlapping = queryset.filter(
        Q(start_date__lte=end_date, end_date__gte=start_date) |
        Q(start_date__lte=start_date, end_date__gte=end_date) |
        Q(start_date__gte=start_date, end_date__lte=end_date)
    )

    if overlapping.exists():
        raise ValidationError(_('Date range overlaps with an existing record.'))


def validate_unique_for_date(queryset, field_name, field_value, date_field_name, date_value, exclude_pk=None):
    """
    Validate that a field is unique for a specific date

    Usage in model's clean():
        validate_unique_for_date(
            queryset=ShiftAssignment.objects,
            field_name='employee',
            field_value=self.employee,
            date_field_name='shift_date',
            date_value=self.shift_date,
            exclude_pk=self.pk
        )
    """
    filters = {
        field_name: field_value,
        date_field_name: date_value
    }

    queryset = queryset.filter(**filters)

    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)

    if queryset.exists():
        raise ValidationError(
            _('A record with this %(field)s already exists for %(date)s.'),
            params={
                'field': field_name,
                'date': date_value
            }
        )


def get_working_days(start_date, end_date, exclude_weekends=True):
    """
    Calculate number of working days between two dates

    Args:
        start_date: Start date
        end_date: End date
        exclude_weekends: Whether to exclude weekends (default: True)

    Returns:
        int: Number of working days
    """
    if not start_date or not end_date:
        return 0

    if end_date < start_date:
        return 0

    days = (end_date - start_date).days + 1

    if exclude_weekends:
        # Count weekends
        current = start_date
        weekend_days = 0
        while current <= end_date:
            if current.weekday() >= 5:  # Saturday or Sunday
                weekend_days += 1
            current += timedelta(days=1)
        days -= weekend_days

    return days


def is_working_day(date_value, exclude_weekends=True):
    """
    Check if a date is a working day

    Args:
        date_value: Date to check
        exclude_weekends: Whether weekends are non-working days

    Returns:
        bool: True if working day
    """
    if exclude_weekends and date_value.weekday() >= 5:
        return False
    return True


def validate_model_dependencies(instance, dependencies):
    """
    Validate that required related objects exist

    Usage in model's clean():
        validate_model_dependencies(self, {
            'department': 'Employee must have a department',
            'position': 'Employee must have a position'
        })
    """
    for field_name, error_message in dependencies.items():
        if not getattr(instance, field_name, None):
            raise ValidationError({field_name: error_message})

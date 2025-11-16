from django.db import models


class Department(models.Model):
    """Department model for managing organizational departments."""

    DEPARTMENT_TYPE_CHOICES = [
        ('PRODUCTION', 'Production'),
        ('SUPPORT', 'Support'),
        ('MANAGEMENT', 'Management'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Department name"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Department description and responsibilities"
    )

    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPE_CHOICES,
        default='OTHER',
        help_text="Category of department"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        db_table = 'hr_department'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['department_type']),
        ]

    def __str__(self):
        return self.name

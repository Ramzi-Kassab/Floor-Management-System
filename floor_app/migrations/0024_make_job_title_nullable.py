# Migration to make job_title field nullable in HREmployee
# The job_title field was replaced with position FK, but the database column still exists
# This migration makes it nullable to allow saves without providing a job_title value
# This allows the new position-based system to work without requiring job_title

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0023_consolidate_address_models'),
    ]

    operations = [
        # Make job_title nullable - it's now deprecated in favor of position FK
        migrations.AlterField(
            model_name='hremployee',
            name='job_title',
            field=models.CharField(
                max_length=128,
                null=True,
                blank=True,
                help_text='DEPRECATED: Use position field instead. Kept for backward compatibility.'
            ),
        ),
    ]

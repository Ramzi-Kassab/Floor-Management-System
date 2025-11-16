# Migration to make employee_type field nullable in HREmployee
# The employee_type field was renamed to contract_type, but the database column still exists with NOT NULL constraint
# This migration makes the column nullable using raw SQL

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0024_make_job_title_nullable'),
    ]

    operations = [
        # Alter the database column to allow NULL values (column already exists in DB)
        migrations.RunSQL(
            sql="ALTER TABLE hr_employee ALTER COLUMN employee_type DROP NOT NULL;",
            reverse_sql="ALTER TABLE hr_employee ALTER COLUMN employee_type SET NOT NULL;",
        ),
    ]

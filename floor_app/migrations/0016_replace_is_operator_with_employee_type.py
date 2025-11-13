# Generated migration to replace is_operator boolean with employee_type choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0015_hraddress_person_hremail_person_hrphone_person_and_more'),
    ]

    operations = [
        # Add new employee_type field with default
        migrations.AddField(
            model_name='hremployee',
            name='employee_type',
            field=models.CharField(
                choices=[
                    ('OPERATOR', 'Floor Operator'),
                    ('SUPERVISOR', 'Supervisor'),
                    ('MANAGER', 'Manager'),
                    ('ENGINEER', 'Engineer'),
                    ('ADMIN', 'Administrative Staff'),
                    ('OTHER', 'Other'),
                ],
                default='OPERATOR',
                help_text='Employee role/type',
                max_length=16,
            ),
        ),
        # Remove old is_operator field
        migrations.RemoveField(
            model_name='hremployee',
            name='is_operator',
        ),
        # Remove preferred_name fields from HRPeople
        migrations.RemoveField(
            model_name='hrpeople',
            name='preferred_name_en',
        ),
        migrations.RemoveField(
            model_name='hrpeople',
            name='preferred_name_ar',
        ),
        # Add help_text to name fields
        migrations.AlterField(
            model_name='hrpeople',
            name='first_name_en',
            field=models.CharField(
                max_length=120,
                help_text='First name in English',
            ),
        ),
        migrations.AlterField(
            model_name='hrpeople',
            name='middle_name_en',
            field=models.CharField(
                max_length=120,
                blank=True,
                default='',
                help_text='Middle name in English (optional)',
            ),
        ),
        migrations.AlterField(
            model_name='hrpeople',
            name='last_name_en',
            field=models.CharField(
                max_length=120,
                help_text='Last name in English',
            ),
        ),
        migrations.AlterField(
            model_name='hrpeople',
            name='first_name_ar',
            field=models.CharField(
                max_length=120,
                blank=True,
                default='',
                help_text='First name in Arabic (optional)',
            ),
        ),
        migrations.AlterField(
            model_name='hrpeople',
            name='middle_name_ar',
            field=models.CharField(
                max_length=120,
                blank=True,
                default='',
                help_text='Middle name in Arabic (optional)',
            ),
        ),
        migrations.AlterField(
            model_name='hrpeople',
            name='last_name_ar',
            field=models.CharField(
                max_length=120,
                blank=True,
                default='',
                help_text='Last name in Arabic (optional)',
            ),
        ),
    ]

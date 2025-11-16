# Migration to consolidate HRAddress into Address model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0022_add_identity_verification_to_hrpeople'),
    ]

    operations = [
        # Add HR-specific fields to Address model
        migrations.AddField(
            model_name='address',
            name='hr_person',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='addresses',
                help_text='HR Person associated with this address (if applicable)',
                to='floor_app.hrpeople'
            ),
        ),

        migrations.AddField(
            model_name='address',
            name='hr_kind',
            field=models.CharField(
                max_length=10,
                blank=True,
                default='',
                choices=[
                    ('HOME', 'Home'),
                    ('OFFICE', 'Office'),
                    ('BILLING', 'Billing'),
                    ('SHIPPING', 'Shipping'),
                    ('OTHER', 'Other'),
                ],
                help_text='Purpose/type of this address (for HR use)'
            ),
        ),

        migrations.AddField(
            model_name='address',
            name='hr_use',
            field=models.CharField(
                max_length=8,
                blank=True,
                default='',
                choices=[
                    ('PERSONAL', 'Personal'),
                    ('BUSINESS', 'Business'),
                ],
                help_text='Personal or business use (for HR use)'
            ),
        ),

        migrations.AddField(
            model_name='address',
            name='is_primary_hint',
            field=models.BooleanField(
                default=False,
                help_text='Is this the primary address for the HR person?'
            ),
        ),

        # Add indexes for HR-specific fields
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['hr_person', 'hr_kind'], name='ops_address_person_kind'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['hr_person', 'is_primary_hint'], name='ops_address_person_primary'),
        ),

        # Delete the old HRAddress model
        migrations.DeleteModel(
            name='HRAddress',
        ),
    ]

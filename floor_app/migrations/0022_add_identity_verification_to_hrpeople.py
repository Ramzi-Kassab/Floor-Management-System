# Generated migration to add identity verification fields to HRPeople

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0021_refactor_hraddress_to_use_generic_address'),
    ]

    operations = [
        # Add marital status field
        migrations.AddField(
            model_name='hrpeople',
            name='marital_status',
            field=models.CharField(
                blank=True,
                choices=[('SINGLE', 'Single'), ('MARRIED', 'Married'), ('DIVORCED', 'Divorced'), ('WIDOWED', 'Widowed')],
                default='',
                help_text='Marital status',
                max_length=16
            ),
        ),

        # Add identity verification flag
        migrations.AddField(
            model_name='hrpeople',
            name='identity_verified',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='Has the identity been verified and authenticated?'
            ),
        ),

        # Add identity verification timestamp
        migrations.AddField(
            model_name='hrpeople',
            name='identity_verified_at',
            field=models.DateTimeField(
                blank=True,
                editable=False,
                help_text='Timestamp of identity verification',
                null=True
            ),
        ),

        # Add identity verification user reference
        migrations.AddField(
            model_name='hrpeople',
            name='identity_verified_by',
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text='User who verified the identity',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='verified_hr_people',
                to=settings.AUTH_USER_MODEL
            ),
        ),

        # Add index for identity_verified lookups
        migrations.AddIndex(
            model_name='hrpeople',
            index=models.Index(fields=['identity_verified'], name='hr_people_verified_idx'),
        ),
    ]

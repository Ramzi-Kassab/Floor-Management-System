# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('floor_core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userthemepreference',
            name='custom_background_color',
            field=models.CharField(
                blank=True,
                help_text='Custom background color in hex format (e.g., #ffffff)',
                max_length=7,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='userthemepreference',
            name='custom_text_color',
            field=models.CharField(
                blank=True,
                help_text='Custom text color in hex format (e.g., #000000)',
                max_length=7,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='userthemepreference',
            name='custom_primary_color',
            field=models.CharField(
                blank=True,
                help_text='Custom primary/accent color in hex format (e.g., #007bff)',
                max_length=7,
                null=True
            ),
        ),
    ]

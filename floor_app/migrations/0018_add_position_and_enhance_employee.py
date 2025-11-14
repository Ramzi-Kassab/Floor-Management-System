# Generated migration to add Position model and enhance HREmployee with contract fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('floor_app', '0017_create_department'),
    ]

    operations = [
        # Create Position model
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Position title (e.g., QA Engineer, Production Operator)', max_length=200, unique=True)),
                ('description', models.TextField(blank=True, help_text='Position description and main responsibilities', null=True)),
                ('position_level', models.CharField(
                    choices=[
                        ('ENTRY', 'Entry Level'),
                        ('JUNIOR', 'Junior'),
                        ('SENIOR', 'Senior'),
                        ('SUPERVISOR', 'Supervisor'),
                        ('MANAGER', 'Manager'),
                        ('DIRECTOR', 'Director'),
                        ('OTHER', 'Other'),
                    ],
                    default='ENTRY',
                    help_text='Seniority level of this position',
                    max_length=16,
                )),
                ('salary_grade', models.CharField(
                    choices=[
                        ('GRADE_A', 'Grade A'),
                        ('GRADE_B', 'Grade B'),
                        ('GRADE_C', 'Grade C'),
                        ('GRADE_D', 'Grade D'),
                        ('GRADE_E', 'Grade E'),
                        ('EXECUTIVE', 'Executive'),
                    ],
                    help_text='Salary grade for this position',
                    max_length=16,
                )),
                ('is_active', models.BooleanField(default=True, help_text='Whether this position is currently available')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user')),
                ('updated_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user')),
                ('remarks', models.CharField(blank=True, default='', max_length=255)),
                ('is_deleted', models.BooleanField(default=False, editable=False)),
                ('deleted_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('department', models.ForeignKey(help_text='Department this position belongs to', on_delete=django.db.models.deletion.PROTECT, related_name='positions', to='floor_app.department')),
            ],
            options={
                'verbose_name': 'Position',
                'verbose_name_plural': 'Positions',
                'db_table': 'hr_position',
                'ordering': ['department', 'name'],
            },
        ),

        # Add Position FK to HREmployee
        migrations.AddField(
            model_name='hremployee',
            name='position',
            field=models.ForeignKey(
                blank=True,
                help_text='Job position/title',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='employees',
                to='floor_app.position',
            ),
        ),

        # Add Department FK to HREmployee
        migrations.AddField(
            model_name='hremployee',
            name='department',
            field=models.ForeignKey(
                blank=True,
                help_text='Department assignment',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='employees',
                to='floor_app.department',
            ),
        ),

        # Add Contract Type (rename employee_type)
        migrations.AddField(
            model_name='hremployee',
            name='contract_type',
            field=models.CharField(
                choices=[
                    ('PERMANENT', 'Permanent Employee'),
                    ('FIXED_TERM', 'Fixed Term Contract'),
                    ('TEMPORARY', 'Temporary'),
                    ('PART_TIME', 'Part-Time'),
                    ('INTERN', 'Internship'),
                    ('CONSULTANT', 'Consultant'),
                    ('CONTRACTOR', 'Contractor'),
                ],
                default='PERMANENT',
                help_text='Type of employment contract',
                max_length=16,
            ),
        ),

        # Add Contract Duration Fields
        migrations.AddField(
            model_name='hremployee',
            name='contract_start_date',
            field=models.DateField(blank=True, help_text='Contract start date (for fixed-term contracts)', null=True),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='contract_end_date',
            field=models.DateField(blank=True, help_text='Contract end date (for fixed-term contracts)', null=True),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='contract_renewal_date',
            field=models.DateField(blank=True, help_text='Next contract renewal date', null=True),
        ),

        # Add Probation Fields
        migrations.AddField(
            model_name='hremployee',
            name='probation_end_date',
            field=models.DateField(blank=True, help_text='Probation period end date', null=True),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='probation_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('PENDING', 'Pending'),
                    ('PASSED', 'Passed'),
                    ('FAILED', 'Failed'),
                ],
                help_text='Current probation status',
                max_length=16,
                null=True,
            ),
        ),

        # Add Work Schedule Fields
        migrations.AddField(
            model_name='hremployee',
            name='work_days_per_week',
            field=models.IntegerField(default=5, help_text='Number of working days per week'),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='hours_per_week',
            field=models.IntegerField(default=40, help_text='Total working hours per week'),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='shift_pattern',
            field=models.CharField(
                choices=[
                    ('DAY', 'Day Shift'),
                    ('NIGHT', 'Night Shift'),
                    ('ROTATING', 'Rotating Shift'),
                    ('FLEXIBLE', 'Flexible'),
                ],
                default='DAY',
                help_text='Work shift pattern',
                max_length=16,
            ),
        ),

        # Add Compensation Fields
        migrations.AddField(
            model_name='hremployee',
            name='salary_grade',
            field=models.CharField(blank=True, default='', help_text='Salary grade classification', max_length=32),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='monthly_salary',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Monthly salary amount', max_digits=12, null=True),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='benefits_eligible',
            field=models.BooleanField(default=True, help_text='Eligible for company benefits'),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='overtime_eligible',
            field=models.BooleanField(default=True, help_text='Eligible for overtime compensation'),
        ),

        # Add Leave Entitlements
        migrations.AddField(
            model_name='hremployee',
            name='annual_leave_days',
            field=models.IntegerField(default=20, help_text='Annual leave days per year'),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='sick_leave_days',
            field=models.IntegerField(default=10, help_text='Sick leave days per year'),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='special_leave_days',
            field=models.IntegerField(default=3, help_text='Special leave days per year'),
        ),

        # Add Employment Details
        migrations.AddField(
            model_name='hremployee',
            name='employment_category',
            field=models.CharField(
                choices=[
                    ('REGULAR', 'Regular'),
                    ('SEASONAL', 'Seasonal'),
                    ('PROJECT_BASED', 'Project-Based'),
                    ('RELIEF_STAFF', 'Relief Staff'),
                    ('CASUAL', 'Casual'),
                ],
                default='REGULAR',
                help_text='Employment category type',
                max_length=20,
            ),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='employment_status',
            field=models.CharField(
                choices=[
                    ('ACTIVE', 'Active'),
                    ('ON_PROBATION', 'On Probation'),
                    ('ON_LEAVE', 'On Leave'),
                    ('ON_SUSPENSION', 'On Suspension'),
                    ('UNDER_NOTICE', 'Under Notice'),
                    ('TERMINATED', 'Terminated'),
                    ('RETIRED', 'Retired'),
                ],
                default='ACTIVE',
                help_text='Current employment status',
                max_length=20,
            ),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='report_to',
            field=models.ForeignKey(
                blank=True,
                help_text='Supervisor or Manager this employee reports to',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='subordinates',
                to='floor_app.hremployee',
            ),
        ),

        migrations.AddField(
            model_name='hremployee',
            name='cost_center',
            field=models.CharField(blank=True, default='', help_text='Cost center code for allocation', max_length=32),
        ),

        # Add indexes to Position model
        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['department', 'name'], name='hr_position_dept_name_idx'),
        ),

        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['position_level'], name='hr_position_level_idx'),
        ),

        migrations.AddIndex(
            model_name='position',
            index=models.Index(fields=['is_active'], name='hr_position_active_idx'),
        ),
    ]

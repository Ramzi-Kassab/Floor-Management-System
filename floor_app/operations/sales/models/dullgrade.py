"""
Sales & Lifecycle - Dull Grade Evaluation
IADC-style dull grading for PDC bits after drilling runs.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .customer import Customer, Rig, Well


class DullGradeEvaluation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Dull grade evaluation for a bit after a drilling run.
    Based on IADC dull grading system.
    Can have multiple evaluations per bit (after each run).
    """
    # IADC Dull Grade Choices
    CUTTING_STRUCTURE_CHOICES = [
        ('0', '0 - No Wear'),
        ('1', '1 - 12.5% Wear'),
        ('2', '2 - 25% Wear'),
        ('3', '3 - 37.5% Wear'),
        ('4', '4 - 50% Wear'),
        ('5', '5 - 62.5% Wear'),
        ('6', '6 - 75% Wear'),
        ('7', '7 - 87.5% Wear'),
        ('8', '8 - 100% Worn Out'),
    ]

    LOCATION_CHOICES = [
        ('N', 'N - Nose'),
        ('M', 'M - Middle'),
        ('G', 'G - Gauge'),
        ('A', 'A - All Areas'),
        ('C', 'C - Cone/Shoulder'),
    ]

    DULL_CHARACTERISTIC_CHOICES = [
        ('BC', 'BC - Broken Cutter'),
        ('BF', 'BF - Bond Failure'),
        ('BT', 'BT - Broken Teeth'),
        ('BU', 'BU - Balled Up'),
        ('CC', 'CC - Cracked Cutter'),
        ('CI', 'CI - Cone Interference'),
        ('CR', 'CR - Cored'),
        ('CT', 'CT - Chipped Tooth'),
        ('ER', 'ER - Erosion'),
        ('FC', 'FC - Flat Crested'),
        ('HC', 'HC - Heat Checking'),
        ('JD', 'JD - Junk Damage'),
        ('LC', 'LC - Lost Cutter'),
        ('LN', 'LN - Lost Nozzle'),
        ('LT', 'LT - Lost Teeth'),
        ('NO', 'NO - No Dull'),
        ('OC', 'OC - Off Center'),
        ('PB', 'PB - Pinched Bit'),
        ('PN', 'PN - Plugged Nozzle'),
        ('RG', 'RG - Rounded Gauge'),
        ('RO', 'RO - Ring Out'),
        ('SD', 'SD - Shirttail Damage'),
        ('SS', 'SS - Self Sharpening'),
        ('TR', 'TR - Tracking'),
        ('WO', 'WO - Washed Out'),
        ('WT', 'WT - Worn Teeth'),
    ]

    GAUGE_CONDITION_CHOICES = [
        ('I', 'I - In Gauge'),
        ('1', '1 - 1/16\" Under'),
        ('2', '2 - 2/16\" Under'),
        ('3', '3 - 3/16\" Under'),
        ('4', '4 - 4/16\" Under'),
        ('5', '5 - 5/16\" Under'),
        ('6', '6 - 6/16\" Under'),
        ('7', '7 - 7/16\" Under'),
        ('8', '8 - 8/16\" Under'),
    ]

    REASON_PULLED_CHOICES = [
        ('BHA', 'BHA - Change BHA'),
        ('CM', 'CM - Condition Mud'),
        ('CP', 'CP - Core Point'),
        ('DMF', 'DMF - Downhole Motor Failure'),
        ('DP', 'DP - Drill Plug'),
        ('DSF', 'DSF - Drill String Failure'),
        ('DST', 'DST - Drill Stem Test'),
        ('DTF', 'DTF - Downhole Tool Failure'),
        ('FM', 'FM - Formation Change'),
        ('HP', 'HP - Hole Problems'),
        ('HR', 'HR - Hours on Bit'),
        ('LOG', 'LOG - Run Logs'),
        ('PP', 'PP - Pump Pressure'),
        ('PR', 'PR - Penetration Rate'),
        ('RIG', 'RIG - Rig Repair'),
        ('TD', 'TD - Total Depth'),
        ('TQ', 'TQ - Torque'),
        ('TW', 'TW - Twist Off'),
        ('WC', 'WC - Weather Conditions'),
        ('WO', 'WO - Washout'),
    ]

    SOURCE_CHOICES = [
        ('RIG_SITE', 'Rig Site Evaluation'),
        ('CUSTOMER_WAREHOUSE', 'Customer Warehouse'),
        ('INTERNAL_EVAL', 'Internal Evaluation (ARDT)'),
        ('DRILLING_CONTRACTOR', 'Drilling Contractor Report'),
        ('THIRD_PARTY', 'Third Party Inspection'),
    ]

    # Identification
    evaluation_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    # Bit Reference (loose coupling)
    serial_unit_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to inventory.SerialUnit"
    )
    bit_serial_number = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Bit serial number (denormalized)"
    )
    mat_number = models.CharField(max_length=50, blank=True, default="")

    # Link to Drilling Run
    drilling_run_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to DrillingRun"
    )
    run_sequence = models.PositiveIntegerField(
        default=1,
        help_text="Which run this evaluation is for"
    )

    # Context
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='dull_grades'
    )
    well = models.ForeignKey(
        Well,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dull_grades'
    )
    rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dull_grades'
    )

    # IADC Dull Grade Components
    # Inner/Outer Cutting Structure Wear
    inner_cutting_structure = models.CharField(
        max_length=1,
        choices=CUTTING_STRUCTURE_CHOICES,
        help_text="Inner 2/3 cutting structure wear (0-8)"
    )
    outer_cutting_structure = models.CharField(
        max_length=1,
        choices=CUTTING_STRUCTURE_CHOICES,
        help_text="Outer 1/3 cutting structure wear (0-8)"
    )

    # Dull Characteristics
    primary_dull_characteristic = models.CharField(
        max_length=3,
        choices=DULL_CHARACTERISTIC_CHOICES,
        help_text="Primary dull characteristic"
    )
    secondary_dull_characteristic = models.CharField(
        max_length=3,
        choices=DULL_CHARACTERISTIC_CHOICES,
        blank=True,
        default="",
        help_text="Secondary characteristic (optional)"
    )

    # Location of Primary Dull
    dull_location = models.CharField(
        max_length=1,
        choices=LOCATION_CHOICES,
        help_text="Location of primary wear"
    )

    # Bearing/Seal (for roller cone - NA for PDC)
    bearing_seal = models.CharField(
        max_length=10,
        blank=True,
        default="X",
        help_text="X for fixed cutter bits"
    )

    # Gauge Condition
    gauge_condition = models.CharField(
        max_length=1,
        choices=GAUGE_CONDITION_CHOICES,
        help_text="Gauge wear measurement"
    )

    # Other Dull Characteristics
    other_dull_characteristic = models.CharField(
        max_length=3,
        choices=DULL_CHARACTERISTIC_CHOICES,
        blank=True,
        default="",
        help_text="Other notable characteristic"
    )

    # Reason Pulled
    reason_pulled = models.CharField(
        max_length=5,
        choices=REASON_PULLED_CHOICES,
        help_text="Why the bit was pulled"
    )

    # Complete IADC Dull Grade String
    iadc_dull_grade = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Complete IADC dull grade string (auto-generated)"
    )

    # Additional Measurements
    cutter_wear_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overall cutter wear percentage"
    )
    gauge_wear_inches = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Actual gauge wear in inches"
    )

    # Detailed Observations
    impact_damage = models.TextField(blank=True, default="")
    abrasion_notes = models.TextField(blank=True, default="")
    thermal_damage = models.TextField(blank=True, default="")
    erosion_notes = models.TextField(blank=True, default="")
    bit_balling_observed = models.BooleanField(default=False)
    cutter_loss_count = models.PositiveIntegerField(default=0)
    blade_damage_notes = models.TextField(blank=True, default="")

    # Photos/Documentation
    photos_json = models.JSONField(
        default=list,
        help_text="List of photo URLs/paths"
    )

    # Evaluation Details
    evaluation_date = models.DateTimeField(default=timezone.now)
    evaluation_source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default='INTERNAL_EVAL'
    )
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dull_grade_evaluations'
    )
    evaluator_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Name if not system user"
    )
    evaluation_location = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    # Recommendations
    recommended_action = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="RERUN, REPAIR, RETROFIT, SCRAP, etc."
    )
    recommendation_notes = models.TextField(blank=True, default="")

    # Quality Link (loose coupling)
    ncr_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Link to quality.NonconformanceReport if issue found"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_dull_grade_evaluation"
        verbose_name = "Dull Grade Evaluation"
        verbose_name_plural = "Dull Grade Evaluations"
        ordering = ['bit_serial_number', '-evaluation_date']
        indexes = [
            models.Index(fields=['evaluation_number'], name='ix_sales_dg_number'),
            models.Index(fields=['serial_unit_id'], name='ix_sales_dg_serial'),
            models.Index(fields=['bit_serial_number'], name='ix_sales_dg_bitsn'),
            models.Index(fields=['customer'], name='ix_sales_dg_customer'),
            models.Index(fields=['evaluation_date'], name='ix_sales_dg_evaldate'),
            models.Index(
                fields=['bit_serial_number', 'run_sequence'],
                name='ix_sales_dg_bit_seq'
            ),
        ]

    def __str__(self):
        return f"{self.evaluation_number} - {self.bit_serial_number} ({self.iadc_dull_grade})"

    @classmethod
    def generate_evaluation_number(cls):
        """Generate unique evaluation number."""
        year = timezone.now().year
        prefix = f"DG-{year}-"
        last_eval = cls.all_objects.filter(
            evaluation_number__startswith=prefix
        ).order_by('-evaluation_number').first()
        if last_eval:
            try:
                last_num = int(last_eval.evaluation_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:06d}"

    def save(self, *args, **kwargs):
        """Generate IADC dull grade string before saving."""
        self.iadc_dull_grade = self.generate_iadc_string()
        super().save(*args, **kwargs)

    def generate_iadc_string(self):
        """
        Generate IADC dull grade string.
        Format: [Inner][Outer]-[Primary]-[Location]-[Bearing]-[Gauge]-[Other]-[Reason]
        Example: 3-4-WT-M-X-I-RG-TD
        """
        parts = [
            self.inner_cutting_structure,
            self.outer_cutting_structure,
            self.primary_dull_characteristic,
            self.dull_location,
            self.bearing_seal or 'X',
            self.gauge_condition,
            self.other_dull_characteristic or 'NO',
            self.reason_pulled,
        ]
        return '-'.join(parts)

    @property
    def severity_score(self):
        """
        Calculate severity score (0-100) based on dull grade.
        Higher = more worn/damaged.
        """
        inner_score = int(self.inner_cutting_structure) * 12.5
        outer_score = int(self.outer_cutting_structure) * 12.5
        avg_wear = (inner_score + outer_score) / 2

        # Adjust for gauge wear
        gauge_penalty = 0
        if self.gauge_condition != 'I':
            gauge_penalty = int(self.gauge_condition) * 5

        # Adjust for severe characteristics
        severe_chars = ['LC', 'LT', 'BF', 'BC', 'WO', 'JD']
        char_penalty = 0
        if self.primary_dull_characteristic in severe_chars:
            char_penalty = 15

        return min(100, avg_wear + gauge_penalty + char_penalty)

    @property
    def is_rerunnable(self):
        """
        Determine if bit can be rerun based on dull grade.
        """
        # Generally rerunnable if wear < 50% and gauge is OK
        inner_wear = int(self.inner_cutting_structure)
        outer_wear = int(self.outer_cutting_structure)
        gauge_ok = self.gauge_condition in ['I', '1', '2']
        no_severe_damage = self.primary_dull_characteristic not in ['LC', 'BF', 'WO', 'JD']

        return inner_wear <= 4 and outer_wear <= 4 and gauge_ok and no_severe_damage

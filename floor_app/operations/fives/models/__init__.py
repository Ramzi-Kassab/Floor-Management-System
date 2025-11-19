"""
5S/Housekeeping Gamification Models

Models for 5S (Sort, Set in Order, Shine, Standardize, Sustain) housekeeping system with gamification.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin


class FiveSAuditTemplate(AuditMixin):
    """Templates for 5S audits."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    area_type = models.CharField(max_length=50, choices=(
        ('OFFICE', 'Office'),
        ('WORKSHOP', 'Workshop'),
        ('WAREHOUSE', 'Warehouse'),
        ('PRODUCTION', 'Production Floor'),
        ('LAB', 'Laboratory'),
        ('OTHER', 'Other'),
    ))

    # Checklist Items
    checklist_items = models.JSONField(default=list, help_text="List of checklist items with scoring")
    total_possible_score = models.IntegerField(default=100)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'fives_audit_templates'
        ordering = ['name']

    def __str__(self):
        return self.name


class FiveSAudit(AuditMixin):
    """5S audit/inspection records."""

    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    audit_number = models.CharField(max_length=50, unique=True)
    template = models.ForeignKey(FiveSAuditTemplate, on_delete=models.PROTECT, related_name='audits')

    # Location
    area_name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    building = models.CharField(max_length=100, blank=True)
    floor_level = models.CharField(max_length=50, blank=True)

    # Team/Responsible
    team_name = models.CharField(max_length=100, blank=True)
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='responsible_audits')
    team_members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='team_audits')

    # Auditor
    audited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='conducted_audits')
    audit_date = models.DateField()
    audit_time = models.TimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    # Scoring
    score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    max_score = models.IntegerField(default=100)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Breakdown by S
    sort_score = models.IntegerField(null=True, blank=True)
    set_in_order_score = models.IntegerField(null=True, blank=True)
    shine_score = models.IntegerField(null=True, blank=True)
    standardize_score = models.IntegerField(null=True, blank=True)
    sustain_score = models.IntegerField(null=True, blank=True)

    # Results
    checklist_responses = models.JSONField(default=dict, help_text="Checklist item responses with scores")
    observations = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    action_items = models.JSONField(default=list, blank=True)

    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)

    # Gamification
    points_awarded = models.IntegerField(default=0, help_text="Gamification points")

    class Meta:
        db_table = 'fives_audits'
        ordering = ['-audit_date']
        indexes = [
            models.Index(fields=['audit_number']),
            models.Index(fields=['area_name', 'audit_date']),
            models.Index(fields=['status', 'audit_date']),
        ]

    def __str__(self):
        return f"{self.audit_number} - {self.area_name}"

    def calculate_percentage(self):
        if self.score is not None and self.max_score > 0:
            self.percentage_score = (self.score / self.max_score) * 100


class FiveSPhoto(AuditMixin):
    """Photos from 5S audits."""

    PHOTO_TYPES = (
        ('BEFORE', 'Before Improvement'),
        ('AFTER', 'After Improvement'),
        ('ISSUE', 'Issue/Problem'),
        ('GOOD_PRACTICE', 'Good Practice'),
        ('EVIDENCE', 'Evidence'),
    )

    audit = models.ForeignKey(FiveSAudit, on_delete=models.CASCADE, related_name='photos')
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPES)
    photo = models.ImageField(upload_to='fives_photos/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    location_in_area = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fives_photos'
        ordering = ['audit', 'photo_type', 'uploaded_date']

    def __str__(self):
        return f"{self.audit.audit_number} - {self.get_photo_type_display()}"


class FiveSLeaderboard(AuditMixin):
    """Leaderboard entries for teams/areas."""

    PERIOD_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    )

    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()

    # Team/Area
    area_name = models.CharField(max_length=200)
    team_name = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Metrics
    total_audits = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_points = models.IntegerField(default=0)
    improvement_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Ranking
    rank = models.IntegerField(null=True, blank=True)

    # Badges/Achievements
    badges_earned = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'fives_leaderboard'
        unique_together = [['period_type', 'period_start', 'area_name']]
        ordering = ['-period_start', 'rank']

    def __str__(self):
        return f"{self.area_name} - {self.period_type} ({self.period_start})"


class FiveSAchievement(AuditMixin):
    """Achievement badges for 5S performance."""

    ACHIEVEMENT_TYPES = (
        ('SCORE', 'High Score'),
        ('CONSISTENCY', 'Consistency'),
        ('IMPROVEMENT', 'Improvement'),
        ('PERFECT', 'Perfect Score'),
        ('CHAMPION', 'Champion'),
        ('MILESTONE', 'Milestone'),
    )

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField(max_length=50, blank=True)
    badge_image = models.ImageField(upload_to='fives_badges/', null=True, blank=True)

    # Criteria
    criteria = models.JSONField(default=dict, help_text="Criteria to earn this achievement")
    points_value = models.IntegerField(default=0, help_text="Points awarded for earning this")

    # Rarity
    rarity = models.CharField(max_length=20, choices=(
        ('COMMON', 'Common'),
        ('UNCOMMON', 'Uncommon'),
        ('RARE', 'Rare'),
        ('EPIC', 'Epic'),
        ('LEGENDARY', 'Legendary'),
    ), default='COMMON')

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'fives_achievements'
        ordering = ['rarity', 'name']

    def __str__(self):
        return self.name


class FiveSUserAchievement(AuditMixin):
    """Achievements earned by users."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fives_achievements')
    achievement = models.ForeignKey(FiveSAchievement, on_delete=models.CASCADE)
    earned_date = models.DateField(auto_now_add=True)

    # Context
    audit = models.ForeignKey(FiveSAudit, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'fives_user_achievements'
        unique_together = [['user', 'achievement']]
        ordering = ['-earned_date']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.achievement.name}"


class FiveSCompetition(AuditMixin):
    """Competitions between teams/areas."""

    STATUS_CHOICES = (
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')

    # Participants (areas/teams)
    participating_areas = models.JSONField(default=list, help_text="List of area names")
    participating_teams = models.JSONField(default=list, help_text="List of team names")

    # Rules
    scoring_method = models.CharField(max_length=50, choices=(
        ('AVERAGE_SCORE', 'Average Audit Score'),
        ('TOTAL_POINTS', 'Total Points'),
        ('IMPROVEMENT', 'Improvement Percentage'),
        ('CUSTOM', 'Custom Scoring'),
    ), default='AVERAGE_SCORE')

    # Prizes/Rewards
    prizes = models.JSONField(default=dict, blank=True, help_text="Prize structure")

    # Results
    winner = models.CharField(max_length=200, blank=True)
    results = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'fives_competitions'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class FiveSImprovementAction(AuditMixin):
    """Improvement actions from audits."""

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('VERIFIED', 'Verified'),
        ('CANCELLED', 'Cancelled'),
    )

    audit = models.ForeignKey(FiveSAudit, on_delete=models.CASCADE, related_name='improvement_actions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=(
        ('SORT', 'Sort (Seiri)'),
        ('SET_IN_ORDER', 'Set in Order (Seiton)'),
        ('SHINE', 'Shine (Seiso)'),
        ('STANDARDIZE', 'Standardize (Seiketsu)'),
        ('SUSTAIN', 'Sustain (Shitsuke)'),
    ))

    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='fives_actions')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_fives_actions')

    # Dates
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Evidence
    before_photo = models.ImageField(upload_to='fives_improvements/before/', null=True, blank=True)
    after_photo = models.ImageField(upload_to='fives_improvements/after/', null=True, blank=True)
    completion_notes = models.TextField(blank=True)

    # Verification
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_fives_actions')
    verification_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'fives_improvement_actions'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.status}"


class FiveSPointsHistory(AuditMixin):
    """History of points earned/spent."""

    TRANSACTION_TYPES = (
        ('AUDIT_COMPLETED', 'Audit Completed'),
        ('HIGH_SCORE', 'High Score Bonus'),
        ('IMPROVEMENT', 'Improvement Bonus'),
        ('ACHIEVEMENT', 'Achievement Earned'),
        ('COMPETITION_WIN', 'Competition Win'),
        ('CONSISTENCY', 'Consistency Bonus'),
        ('PENALTY', 'Penalty'),
        ('REDEMPTION', 'Points Redemption'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fives_points_history')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    points = models.IntegerField(help_text="Positive for earned, negative for spent")
    balance_after = models.IntegerField(help_text="Balance after this transaction")

    # Context
    audit = models.ForeignKey(FiveSAudit, on_delete=models.SET_NULL, null=True, blank=True)
    achievement = models.ForeignKey(FiveSAchievement, on_delete=models.SET_NULL, null=True, blank=True)
    competition = models.ForeignKey(FiveSCompetition, on_delete=models.SET_NULL, null=True, blank=True)

    description = models.CharField(max_length=200)
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fives_points_history'
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.points} pts ({self.get_transaction_type_display()})"

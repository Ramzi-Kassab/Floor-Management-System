"""5S Service - Business logic for 5S housekeeping with gamification"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
from floor_app.operations.fives.models import (
    FiveSAuditTemplate, FiveSAudit, FiveSPhoto, FiveSLeaderboard,
    FiveSAchievement, FiveSUserAchievement, FiveSCompetition,
    FiveSImprovementAction, FiveSPointsHistory
)

User = get_user_model()


class FiveSService:
    """Service for 5S housekeeping management with gamification."""

    # Points configuration
    BASE_AUDIT_POINTS = 10
    HIGH_SCORE_THRESHOLD = 90  # Percentage
    HIGH_SCORE_BONUS = 20
    PERFECT_SCORE_BONUS = 50
    IMPROVEMENT_BONUS_MULTIPLIER = 2  # Points per percentage improvement

    @classmethod
    def generate_audit_number(cls) -> str:
        """Generate unique audit number. Format: 5S-YYYY-NNNN"""
        year = timezone.now().year
        prefix = f"5S-{year}-"

        last_audit = FiveSAudit.objects.filter(
            audit_number__startswith=prefix
        ).order_by('-audit_number').first()

        if last_audit:
            last_number = int(last_audit.audit_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_audit(cls, template_id: int, audited_by: User, data: Dict[str, Any]) -> FiveSAudit:
        """Create a 5S audit."""
        template = FiveSAuditTemplate.objects.get(id=template_id)

        audit_number = cls.generate_audit_number()

        audit = FiveSAudit.objects.create(
            audit_number=audit_number,
            template=template,
            area_name=data['area_name'],
            department=data.get('department', ''),
            building=data.get('building', ''),
            floor_level=data.get('floor_level', ''),
            team_name=data.get('team_name', ''),
            responsible_person_id=data.get('responsible_person_id'),
            audited_by=audited_by,
            audit_date=data['audit_date'],
            audit_time=data.get('audit_time'),
            max_score=template.total_possible_score,
            status='SCHEDULED'
        )

        # Add team members
        if 'team_member_ids' in data:
            audit.team_members.set(User.objects.filter(id__in=data['team_member_ids']))

        return audit

    @classmethod
    @transaction.atomic
    def complete_audit(cls, audit_id: int, checklist_responses: Dict[str, Any],
                       observations: str = '', strengths: str = '',
                       areas_for_improvement: str = '',
                       action_items: List[Dict] = None) -> FiveSAudit:
        """Complete a 5S audit and calculate scores."""
        audit = FiveSAudit.objects.get(id=audit_id)

        # Calculate total score from checklist responses
        total_score = sum(item.get('score', 0) for item in checklist_responses.values())

        # Calculate scores by 5S category
        scores_by_category = {
            'sort': 0,
            'set_in_order': 0,
            'shine': 0,
            'standardize': 0,
            'sustain': 0,
        }

        for item_id, response in checklist_responses.items():
            category = response.get('category', '').lower().replace(' ', '_')
            if category in scores_by_category:
                scores_by_category[category] += response.get('score', 0)

        # Update audit
        audit.status = 'COMPLETED'
        audit.score = total_score
        audit.calculate_percentage()
        audit.checklist_responses = checklist_responses
        audit.observations = observations
        audit.strengths = strengths
        audit.areas_for_improvement = areas_for_improvement
        audit.action_items = action_items or []

        audit.sort_score = scores_by_category['sort']
        audit.set_in_order_score = scores_by_category['set_in_order']
        audit.shine_score = scores_by_category['shine']
        audit.standardize_score = scores_by_category['standardize']
        audit.sustain_score = scores_by_category['sustain']

        audit.save()

        # Award points
        cls.award_points_for_audit(audit)

        # Check for achievements
        if audit.responsible_person:
            cls.check_and_award_achievements(audit.responsible_person, audit)

        # Update leaderboards
        cls.update_leaderboards(audit)

        # Create improvement actions
        if action_items:
            for item in action_items:
                FiveSImprovementAction.objects.create(
                    audit=audit,
                    title=item['title'],
                    description=item.get('description', ''),
                    category=item['category'],
                    assigned_to_id=item['assigned_to_id'],
                    assigned_by=audit.audited_by,
                    due_date=item['due_date']
                )

        return audit

    @classmethod
    def award_points_for_audit(cls, audit: FiveSAudit):
        """Award points for completing an audit."""
        if not audit.responsible_person:
            return

        points = cls.BASE_AUDIT_POINTS

        # Bonus for high score
        if audit.percentage_score >= cls.HIGH_SCORE_THRESHOLD:
            points += cls.HIGH_SCORE_BONUS

        # Bonus for perfect score
        if audit.score == audit.max_score:
            points += cls.PERFECT_SCORE_BONUS

        # Check for improvement
        previous_audit = FiveSAudit.objects.filter(
            area_name=audit.area_name,
            status='COMPLETED',
            audit_date__lt=audit.audit_date
        ).order_by('-audit_date').first()

        if previous_audit and previous_audit.percentage_score:
            improvement = audit.percentage_score - previous_audit.percentage_score
            if improvement > 0:
                improvement_bonus = int(improvement * cls.IMPROVEMENT_BONUS_MULTIPLIER)
                points += improvement_bonus

        # Update audit points
        audit.points_awarded = points
        audit.save()

        # Record points transaction
        current_balance = cls.get_user_points_balance(audit.responsible_person)
        new_balance = current_balance + points

        FiveSPointsHistory.objects.create(
            user=audit.responsible_person,
            transaction_type='AUDIT_COMPLETED',
            points=points,
            balance_after=new_balance,
            audit=audit,
            description=f"Audit completed: {audit.area_name} (Score: {audit.percentage_score}%)"
        )

    @classmethod
    def get_user_points_balance(cls, user: User) -> int:
        """Get user's current points balance."""
        last_transaction = FiveSPointsHistory.objects.filter(user=user).order_by('-transaction_date').first()
        return last_transaction.balance_after if last_transaction else 0

    @classmethod
    def check_and_award_achievements(cls, user: User, audit: FiveSAudit):
        """Check and award achievements based on audit performance."""
        # Perfect Score Achievement
        if audit.score == audit.max_score:
            cls.award_achievement_if_new(user, 'Perfect Score', audit)

        # High Score Achievement (90%+)
        if audit.percentage_score >= 90:
            cls.award_achievement_if_new(user, 'High Achiever', audit)

        # Consistency Achievement (5 audits in a row with 80%+)
        recent_audits = FiveSAudit.objects.filter(
            responsible_person=user,
            status='COMPLETED',
            percentage_score__gte=80
        ).order_by('-audit_date')[:5]

        if recent_audits.count() == 5:
            cls.award_achievement_if_new(user, 'Consistency Champion', audit)

    @classmethod
    def award_achievement_if_new(cls, user: User, achievement_name: str, audit: FiveSAudit):
        """Award achievement if user hasn't earned it yet."""
        try:
            achievement = FiveSAchievement.objects.get(name=achievement_name, is_active=True)

            # Check if already earned
            if not FiveSUserAchievement.objects.filter(user=user, achievement=achievement).exists():
                FiveSUserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    audit=audit,
                    reason=f"Earned during audit {audit.audit_number}"
                )

                # Award points for achievement
                current_balance = cls.get_user_points_balance(user)
                new_balance = current_balance + achievement.points_value

                FiveSPointsHistory.objects.create(
                    user=user,
                    transaction_type='ACHIEVEMENT',
                    points=achievement.points_value,
                    balance_after=new_balance,
                    achievement=achievement,
                    description=f"Achievement unlocked: {achievement.name}"
                )
        except FiveSAchievement.DoesNotExist:
            pass

    @classmethod
    def update_leaderboards(cls, audit: FiveSAudit):
        """Update leaderboards after audit completion."""
        # Determine current period
        today = timezone.now().date()

        # Weekly leaderboard
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        cls._update_leaderboard_entry('WEEKLY', week_start, week_end, audit.area_name, audit.responsible_person)

        # Monthly leaderboard
        month_start = today.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        cls._update_leaderboard_entry('MONTHLY', month_start, month_end, audit.area_name, audit.responsible_person)

    @classmethod
    def _update_leaderboard_entry(cls, period_type: str, period_start: date, period_end: date,
                                   area_name: str, responsible_person: User):
        """Update or create a leaderboard entry."""
        # Get audits for this period and area
        audits = FiveSAudit.objects.filter(
            area_name=area_name,
            audit_date__gte=period_start,
            audit_date__lte=period_end,
            status='COMPLETED'
        )

        if not audits.exists():
            return

        # Calculate metrics
        total_audits = audits.count()
        average_score = audits.aggregate(avg=Avg('percentage_score'))['avg'] or 0
        total_points = audits.aggregate(sum=Sum('points_awarded'))['sum'] or 0

        # Get or create leaderboard entry
        entry, created = FiveSLeaderboard.objects.update_or_create(
            period_type=period_type,
            period_start=period_start,
            area_name=area_name,
            defaults={
                'period_end': period_end,
                'responsible_person': responsible_person,
                'total_audits': total_audits,
                'average_score': Decimal(str(average_score)),
                'total_points': total_points,
            }
        )

        # Update rankings
        cls._update_rankings(period_type, period_start)

    @classmethod
    def _update_rankings(cls, period_type: str, period_start: date):
        """Update rankings for a leaderboard period."""
        entries = FiveSLeaderboard.objects.filter(
            period_type=period_type,
            period_start=period_start
        ).order_by('-average_score', '-total_points')

        for rank, entry in enumerate(entries, start=1):
            entry.rank = rank
            entry.save(update_fields=['rank'])

    @classmethod
    def get_leaderboard(cls, period_type: str = 'MONTHLY', limit: int = 10) -> List[FiveSLeaderboard]:
        """Get current leaderboard."""
        today = timezone.now().date()

        if period_type == 'WEEKLY':
            period_start = today - timedelta(days=today.weekday())
        elif period_type == 'MONTHLY':
            period_start = today.replace(day=1)
        elif period_type == 'QUARTERLY':
            quarter = (today.month - 1) // 3
            period_start = today.replace(month=quarter * 3 + 1, day=1)
        else:  # YEARLY
            period_start = today.replace(month=1, day=1)

        return list(FiveSLeaderboard.objects.filter(
            period_type=period_type,
            period_start=period_start
        ).order_by('rank')[:limit])

    @classmethod
    def get_user_statistics(cls, user: User) -> Dict[str, Any]:
        """Get user's 5S statistics."""
        audits = FiveSAudit.objects.filter(responsible_person=user, status='COMPLETED')

        return {
            'total_audits': audits.count(),
            'average_score': audits.aggregate(avg=Avg('percentage_score'))['avg'] or 0,
            'highest_score': audits.aggregate(max=models.Max('percentage_score'))['max'] or 0,
            'total_points': cls.get_user_points_balance(user),
            'achievements_count': FiveSUserAchievement.objects.filter(user=user).count(),
            'recent_audits': list(audits.order_by('-audit_date')[:5]),
        }

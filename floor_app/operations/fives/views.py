"""
FIVES Audit System Views

Template-rendering views for 5S audits, leaderboards, and achievements.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    FiveSAudit,
    FiveSPhoto,
    FiveSAchievement,
    FiveSLeaderboard,
)


@login_required
def audit_list(request):
    """
    List all 5S audits.

    Shows:
    - Recent audits
    - Filter by area, status, auditor
    - Statistics
    """
    try:
        audits = FiveSAudit.objects.select_related(
            'audited_by',
            'location',
            'department'
        ).annotate(
            average_score=Avg('scores__score')
        ).order_by('-audit_date')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            audits = audits.filter(status=status_filter)

        # Filter by department
        department_id = request.GET.get('department')
        if department_id:
            audits = audits.filter(department_id=department_id)

        # Filter by date range
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if from_date:
            audits = audits.filter(audit_date__gte=from_date)
        if to_date:
            audits = audits.filter(audit_date__lte=to_date)

        # Statistics
        stats = {
            'total': FiveSAudit.objects.count(),
            'completed': FiveSAudit.objects.filter(status='COMPLETED').count(),
            'in_progress': FiveSAudit.objects.filter(status='IN_PROGRESS').count(),
            'average_score': FiveSAudit.objects.aggregate(avg=Avg('score'))['avg'] or 0,
        }

        context = {
            'audits': audits,
            'stats': stats,
            'status_choices': FiveSAudit.STATUS_CHOICES,
            'status_filter': status_filter,
            'page_title': '5S Audit List',
        }

    except Exception as e:
        messages.error(request, f'Error loading audits: {str(e)}')
        context = {
            'audits': [],
            'stats': {},
            'page_title': '5S Audit List',
        }

    return render(request, 'fives/audit_list.html', context)


@login_required
def audit_form(request, pk=None):
    """
    Create or edit 5S audit.

    Handles:
    - New audit creation
    - Audit editing
    - Score entry for each S
    """
    try:
        audit = None
        if pk:
            audit = get_object_or_404(FiveSAudit, pk=pk)

        if request.method == 'POST':
            try:
                audit_date = request.POST.get('audit_date')
                area = request.POST.get('area')
                notes = request.POST.get('notes', '')

                # Scores for each S
                sort_score = request.POST.get('sort_score')
                set_in_order_score = request.POST.get('set_in_order_score')
                shine_score = request.POST.get('shine_score')
                standardize_score = request.POST.get('standardize_score')
                sustain_score = request.POST.get('sustain_score')

                if audit:
                    # Update existing
                    audit.audit_date = audit_date
                    audit.area = area
                    audit.notes = notes
                    audit.save()
                    action = 'updated'
                else:
                    # Create new
                    audit = FiveSAudit.objects.create(
                        audit_date=audit_date,
                        area=area,
                        notes=notes,
                        audited_by=request.user,
                        status='IN_PROGRESS'
                    )
                    action = 'created'

                # Update scores
                if sort_score:
                    FiveSAudit.objects.update_or_create(
                        audit=audit,
                        s_type='SORT',
                        defaults={'score': int(sort_score)}
                    )

                if set_in_order_score:
                    FiveSAudit.objects.update_or_create(
                        audit=audit,
                        s_type='SET_IN_ORDER',
                        defaults={'score': int(set_in_order_score)}
                    )

                if shine_score:
                    FiveSAudit.objects.update_or_create(
                        audit=audit,
                        s_type='SHINE',
                        defaults={'score': int(shine_score)}
                    )

                if standardize_score:
                    FiveSAudit.objects.update_or_create(
                        audit=audit,
                        s_type='STANDARDIZE',
                        defaults={'score': int(standardize_score)}
                    )

                if sustain_score:
                    FiveSAudit.objects.update_or_create(
                        audit=audit,
                        s_type='SUSTAIN',
                        defaults={'score': int(sustain_score)}
                    )

                # Mark as completed if requested
                if request.POST.get('complete') == 'on':
                    audit.status = 'COMPLETED'
                    audit.completed_at = timezone.now()
                    audit.save()

                messages.success(request, f'Audit {action} successfully.')
                return redirect('fives:audit_detail', pk=audit.pk)

            except Exception as e:
                messages.error(request, f'Error saving audit: {str(e)}')

        # Get existing scores if editing
        scores = {}
        if audit:
            for score in audit.scores.all():
                scores[score.s_type] = score.score

        context = {
            'audit': audit,
            'scores': scores,
            'is_edit': pk is not None,
            'page_title': 'Edit Audit' if pk else 'New Audit',
        }

    except Exception as e:
        messages.error(request, f'Error loading audit form: {str(e)}')
        return redirect('fives:audit_list')

    return render(request, 'fives/audit_form.html', context)


@login_required
def audit_detail(request, pk):
    """
    View audit details.

    Shows:
    - Audit information
    - Scores for each S
    - Photos
    - Checklist items
    """
    try:
        audit = get_object_or_404(
            FiveSAudit.objects.select_related('audited_by', 'location', 'department'),
            pk=pk
        )

        # Get scores
        scores = audit.scores.all()

        # Calculate average score
        score_values = [s.score for s in scores]
        average_score = sum(score_values) / len(score_values) if score_values else 0

        # Get photos
        photos = audit.photos.all()

        # Get checklist items
        checklist_items = audit.checklist_items.all()

        context = {
            'audit': audit,
            'scores': scores,
            'average_score': average_score,
            'photos': photos,
            'checklist_items': checklist_items,
            'page_title': f'Audit - {audit.area}',
        }

    except Exception as e:
        messages.error(request, f'Error loading audit: {str(e)}')
        return redirect('fives:audit_list')

    return render(request, 'fives/audit_detail.html', context)


@login_required
def leaderboard(request):
    """
    View 5S leaderboard.

    Shows:
    - Top performing areas
    - Best auditors
    - Score trends
    """
    try:
        # Get top areas by average score
        top_areas = FiveSAudit.objects.values('area').annotate(
            avg_score=Avg('scores__score'),
            audit_count=Count('id')
        ).order_by('-avg_score')[:10]

        # Get top auditors
        top_auditors = FiveSAudit.objects.values('audited_by__username').annotate(
            audit_count=Count('id'),
            avg_score=Avg('scores__score')
        ).order_by('-audit_count')[:10]

        # Recent high scores
        recent_high_scores = FiveSAudit.objects.filter(
            status='COMPLETED'
        ).annotate(
            avg_score=Avg('scores__score')
        ).filter(avg_score__gte=80).order_by('-audit_date')[:10]

        # This month's stats
        this_month_start = timezone.now().replace(day=1)
        this_month_audits = FiveSAudit.objects.filter(
            audit_date__gte=this_month_start
        )

        month_stats = {
            'total_audits': this_month_audits.count(),
            'average_score': this_month_audits.aggregate(avg=Avg('scores__score'))['avg'] or 0,
            'completed': this_month_audits.filter(status='COMPLETED').count(),
        }

        context = {
            'top_areas': top_areas,
            'top_auditors': top_auditors,
            'recent_high_scores': recent_high_scores,
            'month_stats': month_stats,
            'page_title': '5S Leaderboard',
        }

    except Exception as e:
        messages.error(request, f'Error loading leaderboard: {str(e)}')
        context = {
            'top_areas': [],
            'top_auditors': [],
            'recent_high_scores': [],
            'month_stats': {},
            'page_title': '5S Leaderboard',
        }

    return render(request, 'fives/leaderboard.html', context)


@login_required
def achievements(request):
    """
    View achievements and badges.

    Shows:
    - User's achievements
    - Available achievements
    - Progress tracking
    """
    try:
        user = request.user

        # Get user's achievements
        user_achievements = FiveSAchievement.objects.filter(
            earned_by=user
        ).order_by('-earned_at')

        # Get all available achievements
        all_achievements = FiveSAchievement.objects.values('achievement_type', 'title').distinct()

        # User stats
        user_stats = {
            'total_audits': FiveSAudit.objects.filter(audited_by=user).count(),
            'completed_audits': FiveSAudit.objects.filter(audited_by=user, status='COMPLETED').count(),
            'average_score': FiveSAudit.objects.filter(audited_by=user).aggregate(avg=Avg('scores__score'))['avg'] or 0,
            'total_achievements': user_achievements.count(),
        }

        context = {
            'user_achievements': user_achievements,
            'all_achievements': all_achievements,
            'user_stats': user_stats,
            'page_title': 'Achievements',
        }

    except Exception as e:
        messages.error(request, f'Error loading achievements: {str(e)}')
        context = {
            'user_achievements': [],
            'all_achievements': [],
            'user_stats': {},
            'page_title': 'Achievements',
        }

    return render(request, 'fives/achievements.html', context)

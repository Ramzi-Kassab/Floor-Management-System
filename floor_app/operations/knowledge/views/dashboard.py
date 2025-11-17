"""
Dashboard views for Knowledge & Instructions module.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from ..models import (
    Article, InstructionRule, TrainingCourse, TrainingEnrollment,
    Category, FAQEntry, Document
)
from ..services import KnowledgeService


@login_required
def knowledge_dashboard(request):
    """Main dashboard for Knowledge & Instructions module."""

    # Get statistics
    article_stats = KnowledgeService.get_article_stats()

    # Recent articles
    recent_articles = KnowledgeService.get_recent_articles(limit=5)

    # Featured articles
    featured_articles = KnowledgeService.get_featured_articles(limit=3)

    # Articles needing review
    articles_needing_review = KnowledgeService.get_articles_needing_review()[:5]

    # Active instructions
    active_instructions = InstructionRule.objects.filter(
        status=InstructionRule.Status.ACTIVE,
        is_deleted=False
    ).count()

    # Temporary instructions expiring soon
    expiring_instructions = InstructionRule.objects.filter(
        status=InstructionRule.Status.ACTIVE,
        is_temporary=True,
        valid_until__isnull=False,
        valid_until__lte=timezone.now() + timedelta(days=7),
        is_deleted=False
    ).order_by('valid_until')[:5]

    # Training overview
    published_courses = TrainingCourse.objects.filter(
        status=TrainingCourse.Status.PUBLISHED,
        is_deleted=False
    ).count()

    # User's training (if they have an employee record)
    user_training = None
    if hasattr(request.user, 'employee'):
        employee = request.user.employee
        user_enrollments = TrainingEnrollment.objects.filter(employee=employee)
        user_training = {
            'in_progress': user_enrollments.filter(
                status=TrainingEnrollment.Status.IN_PROGRESS
            ).count(),
            'completed': user_enrollments.filter(
                status=TrainingEnrollment.Status.COMPLETED
            ).count(),
            'expiring_soon': user_enrollments.filter(
                status=TrainingEnrollment.Status.COMPLETED,
                expires_at__isnull=False,
                expires_at__lte=timezone.now() + timedelta(days=30)
            ).count()
        }

    # Popular FAQs
    popular_faqs = FAQEntry.objects.filter(
        is_published=True,
        is_featured=True,
        is_deleted=False
    ).order_by('-view_count')[:5]

    # Categories with article counts
    categories = Category.objects.filter(
        is_active=True,
        is_deleted=False,
        parent__isnull=True
    ).annotate(
        article_count=Count('articles', filter=Q(articles__is_deleted=False))
    ).order_by('-article_count')[:8]

    # Recent documents
    recent_documents = Document.objects.filter(
        is_deleted=False
    ).order_by('-created_at')[:5]

    context = {
        'article_stats': article_stats,
        'recent_articles': recent_articles,
        'featured_articles': featured_articles,
        'articles_needing_review': articles_needing_review,
        'active_instructions': active_instructions,
        'expiring_instructions': expiring_instructions,
        'published_courses': published_courses,
        'user_training': user_training,
        'popular_faqs': popular_faqs,
        'categories': categories,
        'recent_documents': recent_documents,
    }

    return render(request, 'knowledge/dashboard.html', context)


@login_required
def knowledge_stats_api(request):
    """API endpoint for dashboard statistics (for auto-refresh)."""
    stats = KnowledgeService.get_article_stats()

    active_instructions = InstructionRule.objects.filter(
        status=InstructionRule.Status.ACTIVE,
        is_deleted=False
    ).count()

    return JsonResponse({
        'articles': stats,
        'active_instructions': active_instructions,
        'published_courses': TrainingCourse.objects.filter(
            status=TrainingCourse.Status.PUBLISHED,
            is_deleted=False
        ).count(),
    })

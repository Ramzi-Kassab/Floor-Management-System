"""
Global search view.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import Article, InstructionRule, TrainingCourse, FAQEntry, Document


@login_required
def global_search(request):
    """Search across all knowledge content."""
    query = request.GET.get('q', '')
    results = {
        'articles': [],
        'instructions': [],
        'courses': [],
        'faqs': [],
        'documents': [],
    }

    if query and len(query) >= 2:
        # Search articles
        results['articles'] = Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        ).filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(body__icontains=query) |
            Q(code__icontains=query)
        )[:10]

        # Search instructions
        results['instructions'] = InstructionRule.objects.filter(
            status=InstructionRule.Status.ACTIVE,
            is_deleted=False
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(code__icontains=query)
        )[:10]

        # Search courses
        results['courses'] = TrainingCourse.objects.filter(
            status=TrainingCourse.Status.PUBLISHED,
            is_deleted=False
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(code__icontains=query)
        )[:10]

        # Search FAQs
        results['faqs'] = FAQEntry.objects.filter(
            is_published=True,
            is_deleted=False
        ).filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        )[:10]

        # Search documents
        results['documents'] = Document.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:10]

    total_results = sum(len(r) for r in results.values())

    context = {
        'query': query,
        'results': results,
        'total_results': total_results,
    }

    return render(request, 'knowledge/search_results.html', context)

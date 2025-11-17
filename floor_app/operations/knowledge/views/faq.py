"""
FAQ views.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import FAQGroup, FAQEntry


@login_required
def faq_list(request):
    """List all FAQ groups and entries."""
    groups = FAQGroup.objects.filter(
        is_active=True,
        is_deleted=False
    ).prefetch_related('entries').order_by('order')

    # Search
    query = request.GET.get('q', '')
    if query:
        from django.db.models import Q
        entries = FAQEntry.objects.filter(
            is_published=True,
            is_deleted=False
        ).filter(
            Q(question__icontains=query) |
            Q(answer__icontains=query) |
            Q(keywords__icontains=query)
        ).order_by('-is_featured', '-helpful_count')
    else:
        entries = None

    context = {
        'groups': groups,
        'search_results': entries,
        'query': query,
    }

    return render(request, 'knowledge/faq_list.html', context)


@login_required
def faq_mark_helpful(request, pk):
    """Mark FAQ as helpful or not."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    entry = get_object_or_404(FAQEntry, pk=pk, is_published=True, is_deleted=False)

    helpful = request.POST.get('helpful', 'true') == 'true'
    entry.mark_helpful(helpful)

    return JsonResponse({
        'success': True,
        'helpful_count': entry.helpful_count,
        'not_helpful_count': entry.not_helpful_count,
        'helpfulness_score': entry.helpfulness_score
    })

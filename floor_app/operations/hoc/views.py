"""
Health and Observation Card (HOC) System Views

Template-rendering views for safety observations and reporting.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    HazardObservation,
    HazardCategory,
    HOCComment,
)


@login_required
def observation_list(request):
    """List all HOC observations."""
    try:
        observations = HazardObservation.objects.select_related(
            'reported_by',
            'category',
            'location'
        ).order_by('-observation_date')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            observations = observations.filter(status=status_filter)

        # Filter by severity
        severity_filter = request.GET.get('severity')
        if severity_filter:
            observations = observations.filter(severity=severity_filter)

        # Filter by category
        category_id = request.GET.get('category')
        if category_id:
            observations = observations.filter(category_id=category_id)

        # Search
        search = request.GET.get('q')
        if search:
            observations = observations.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__name__icontains=search)
            )

        # Get categories for filter
        categories = HazardCategory.objects.filter(is_active=True)

        # Statistics
        stats = {
            'total': HazardObservation.objects.count(),
            'open': HazardObservation.objects.filter(status='OPEN').count(),
            'in_progress': HazardObservation.objects.filter(status='IN_PROGRESS').count(),
            'closed': HazardObservation.objects.filter(status='CLOSED').count(),
            'critical': HazardObservation.objects.filter(severity='CRITICAL').count(),
        }

        context = {
            'observations': observations,
            'categories': categories,
            'stats': stats,
            'status_choices': HazardObservation.STATUS_CHOICES,
            'severity_choices': HazardObservation.SEVERITY_CHOICES,
            'page_title': 'HOC Observations',
        }

    except Exception as e:
        messages.error(request, f'Error loading observations: {str(e)}')
        context = {'observations': [], 'categories': [], 'stats': {}, 'page_title': 'HOC Observations'}

    return render(request, 'hoc/observation_list.html', context)


@login_required
def submit_hoc(request):
    """Submit new HOC observation."""
    try:
        if request.method == 'POST':
            try:
                title = request.POST.get('title')
                description = request.POST.get('description')
                category_id = request.POST.get('category')
                severity = request.POST.get('severity')
                location_id = request.POST.get('location')
                observation_type = request.POST.get('observation_type')

                if not all([title, description, category_id, severity]):
                    messages.error(request, 'Please fill in all required fields.')
                else:
                    observation = HazardObservation.objects.create(
                        title=title,
                        description=description,
                        category_id=category_id,
                        severity=severity,
                        observation_type=observation_type,
                        reported_by=request.user,
                        observation_date=timezone.now(),
                        status='OPEN'
                    )

                    if location_id:
                        observation.location_id = location_id
                        observation.save()

                    messages.success(request, 'HOC observation submitted successfully.')
                    return redirect('hoc:observation_detail', pk=observation.pk)

            except Exception as e:
                messages.error(request, f'Error submitting observation: {str(e)}')

        # Get categories
        categories = HazardCategory.objects.filter(is_active=True)

        context = {
            'categories': categories,
            'severity_choices': HazardObservation.SEVERITY_CHOICES,
            'observation_types': HazardObservation.OBSERVATION_TYPES,
            'page_title': 'Submit HOC',
        }

    except Exception as e:
        messages.error(request, f'Error loading form: {str(e)}')
        context = {'categories': [], 'page_title': 'Submit HOC'}

    return render(request, 'hoc/submit_hoc.html', context)


@login_required
def observation_detail(request, pk):
    """View observation details."""
    try:
        observation = get_object_or_404(
            HazardObservation.objects.select_related(
                'reported_by',
                'category',
                'location',
                'assigned_to'
            ),
            pk=pk
        )

        if request.method == 'POST':
            action = request.POST.get('action')

            try:
                if action == 'update_status':
                    new_status = request.POST.get('status')
                    observation.status = new_status

                    if new_status == 'CLOSED':
                        observation.closed_at = timezone.now()

                    observation.save()
                    messages.success(request, 'Status updated successfully.')

                elif action == 'add_action':
                    action_description = request.POST.get('action_description')
                    if action_description:
                        HOCComment.objects.create(
                            observation=observation,
                            action_description=action_description,
                            action_by=request.user,
                            action_date=timezone.now()
                        )
                        messages.success(request, 'Action added successfully.')

                return redirect('hoc:observation_detail', pk=pk)

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        # Get actions
        actions = observation.actions.select_related('action_by').order_by('-action_date')

        context = {
            'observation': observation,
            'actions': actions,
            'status_choices': HazardObservation.STATUS_CHOICES,
            'page_title': f'HOC - {observation.title}',
        }

    except Exception as e:
        messages.error(request, f'Error loading observation: {str(e)}')
        return redirect('hoc:observation_list')

    return render(request, 'hoc/observation_detail.html', context)


@login_required
def hoc_analytics(request):
    """HOC analytics and reports."""
    try:
        # Statistics by category
        by_category = HazardObservation.objects.values(
            'category__name'
        ).annotate(count=Count('id')).order_by('-count')

        # Statistics by severity
        by_severity = HazardObservation.objects.values(
            'severity'
        ).annotate(count=Count('id'))

        # Monthly trend
        from django.db.models.functions import TruncMonth
        monthly_trend = HazardObservation.objects.annotate(
            month=TruncMonth('observation_date')
        ).values('month').annotate(count=Count('id')).order_by('month')

        # Top reporters
        top_reporters = HazardObservation.objects.values(
            'reported_by__username'
        ).annotate(count=Count('id')).order_by('-count')[:10]

        # Overall stats
        stats = {
            'total_observations': HazardObservation.objects.count(),
            'open': HazardObservation.objects.filter(status='OPEN').count(),
            'critical': HazardObservation.objects.filter(severity='CRITICAL').count(),
            'this_month': HazardObservation.objects.filter(
                observation_date__gte=timezone.now().replace(day=1)
            ).count(),
        }

        context = {
            'by_category': by_category,
            'by_severity': by_severity,
            'monthly_trend': monthly_trend,
            'top_reporters': top_reporters,
            'stats': stats,
            'page_title': 'HOC Analytics',
        }

    except Exception as e:
        messages.error(request, f'Error loading analytics: {str(e)}')
        context = {'stats': {}, 'page_title': 'HOC Analytics'}

    return render(request, 'hoc/hoc_analytics.html', context)

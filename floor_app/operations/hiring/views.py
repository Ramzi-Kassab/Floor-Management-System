"""
Hiring & Recruitment System Views

Template-rendering views for job postings, candidates, applications, and interviews.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    JobPosting,
    Candidate,
    JobApplication,
    Interview,
    JobOffer,
)


@login_required
def job_list(request):
    """List all job postings."""
    try:
        jobs = JobPosting.objects.annotate(
            application_count=Count('applications')
        ).order_by('-is_active', '-posted_date')

        status_filter = request.GET.get('status')
        if status_filter == 'active':
            jobs = jobs.filter(is_active=True)
        elif status_filter == 'closed':
            jobs = jobs.filter(is_active=False)

        search = request.GET.get('q')
        if search:
            jobs = jobs.filter(
                Q(job_title__icontains=search) |
                Q(department__icontains=search) |
                Q(location__icontains=search)
            )

        stats = {
            'total': JobPosting.objects.count(),
            'active': JobPosting.objects.filter(is_active=True).count(),
            'total_applications': JobApplication.objects.count(),
        }

        context = {
            'jobs': jobs,
            'stats': stats,
            'page_title': 'Job Postings',
        }

    except Exception as e:
        messages.error(request, f'Error loading jobs: {str(e)}')
        context = {'jobs': [], 'stats': {}, 'page_title': 'Job Postings'}

    return render(request, 'hiring/job_list.html', context)


@login_required
def candidate_list(request):
    """List all candidates."""
    try:
        candidates = Candidate.objects.annotate(
            application_count=Count('applications')
        ).order_by('-created_at')

        search = request.GET.get('q')
        if search:
            candidates = candidates.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )

        stats = {
            'total': Candidate.objects.count(),
            'with_applications': Candidate.objects.filter(applications__isnull=False).distinct().count(),
        }

        context = {
            'candidates': candidates,
            'stats': stats,
            'page_title': 'Candidates',
        }

    except Exception as e:
        messages.error(request, f'Error loading candidates: {str(e)}')
        context = {'candidates': [], 'stats': {}, 'page_title': 'Candidates'}

    return render(request, 'hiring/candidate_list.html', context)


@login_required
def application_detail(request, pk):
    """View application details."""
    try:
        application = get_object_or_404(
            JobApplication.objects.select_related(
                'job_posting',
                'candidate',
                'reviewed_by'
            ),
            pk=pk
        )

        if request.method == 'POST':
            action = request.POST.get('action')

            try:
                if action == 'update_status':
                    new_status = request.POST.get('status')
                    notes = request.POST.get('notes', '')

                    application.status = new_status
                    application.reviewed_by = request.user
                    application.reviewed_at = timezone.now()
                    if notes:
                        application.notes = notes
                    application.save()

                    messages.success(request, 'JobApplication status updated.')
                    return redirect('hiring:application_detail', pk=pk)

            except Exception as e:
                messages.error(request, f'Error updating application: {str(e)}')

        # Get interviews for this application
        interviews = application.interviews.select_related(
            'interviewer'
        ).order_by('-scheduled_at')

        context = {
            'application': application,
            'interviews': interviews,
            'status_choices': JobApplication.STATUS_CHOICES,
            'page_title': f'JobApplication - {application.candidate.full_name}',
        }

    except Exception as e:
        messages.error(request, f'Error loading application: {str(e)}')
        return redirect('hiring:candidate_list')

    return render(request, 'hiring/application_detail.html', context)


@login_required
def interview_scheduler(request):
    """Schedule and manage interviews."""
    try:
        interviews = Interview.objects.select_related(
            'application__candidate',
            'application__job_posting',
            'interviewer'
        ).order_by('-scheduled_at')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            interviews = interviews.filter(status=status_filter)

        # Filter upcoming/past
        time_filter = request.GET.get('time')
        if time_filter == 'upcoming':
            interviews = interviews.filter(scheduled_at__gte=timezone.now())
        elif time_filter == 'past':
            interviews = interviews.filter(scheduled_at__lt=timezone.now())

        if request.method == 'POST':
            try:
                application_id = request.POST.get('application_id')
                scheduled_at = request.POST.get('scheduled_at')
                interview_type = request.POST.get('interview_type')
                location = request.POST.get('location', '')
                notes = request.POST.get('notes', '')

                if application_id and scheduled_at:
                    application = JobApplication.objects.get(pk=application_id)

                    Interview.objects.create(
                        application=application,
                        scheduled_at=scheduled_at,
                        interview_type=interview_type,
                        location=location,
                        notes=notes,
                        interviewer=request.user,
                        status='SCHEDULED'
                    )

                    messages.success(request, 'Interview scheduled successfully.')
                    return redirect('hiring:interview_scheduler')

            except Exception as e:
                messages.error(request, f'Error scheduling interview: {str(e)}')

        # Get pending applications for scheduling
        pending_applications = JobApplication.objects.filter(
            status='UNDER_REVIEW'
        ).select_related('candidate', 'job_posting')

        stats = {
            'total': Interview.objects.count(),
            'scheduled': Interview.objects.filter(status='SCHEDULED').count(),
            'completed': Interview.objects.filter(status='COMPLETED').count(),
        }

        context = {
            'interviews': interviews,
            'pending_applications': pending_applications,
            'stats': stats,
            'status_choices': Interview.STATUS_CHOICES,
            'interview_types': Interview.INTERVIEW_TYPES,
            'page_title': 'Interview Scheduler',
        }

    except Exception as e:
        messages.error(request, f'Error loading interviews: {str(e)}')
        context = {'interviews': [], 'pending_applications': [], 'stats': {}, 'page_title': 'Interview Scheduler'}

    return render(request, 'hiring/interview_scheduler.html', context)


@login_required
def offer_list(request):
    """List all job offers."""
    try:
        offers = JobOffer.objects.select_related(
            'application__candidate',
            'application__job_posting',
            'offered_by'
        ).order_by('-offer_date')

        status_filter = request.GET.get('status')
        if status_filter:
            offers = offers.filter(status=status_filter)

        stats = {
            'total': JobOffer.objects.count(),
            'pending': JobOffer.objects.filter(status='PENDING').count(),
            'accepted': JobOffer.objects.filter(status='ACCEPTED').count(),
            'rejected': JobOffer.objects.filter(status='REJECTED').count(),
        }

        context = {
            'offers': offers,
            'stats': stats,
            'status_choices': JobOffer.STATUS_CHOICES,
            'page_title': 'Job Offers',
        }

    except Exception as e:
        messages.error(request, f'Error loading offers: {str(e)}')
        context = {'offers': [], 'stats': {}, 'page_title': 'Job Offers'}

    return render(request, 'hiring/offer_list.html', context)

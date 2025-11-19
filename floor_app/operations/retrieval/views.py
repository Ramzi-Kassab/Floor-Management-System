"""
Retrieval System Views

Template-rendering views for retrieval requests and supervisor approvals.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType

from .models import RetrievalRequest, RetrievalMetric
from .forms import (
    RetrievalRequestForm,
    SupervisorApprovalForm,
    RetrievalFilterForm,
    BulkApprovalForm
)
from .services import RetrievalService


@login_required
def retrieval_dashboard(request):
    """
    Display user's retrieval request history.

    Shows:
    - User's submitted retrieval requests
    - Status badges and indicators
    - Time elapsed information
    - Supervisor action tracking
    - Employee accuracy metrics
    """
    user = request.user

    # Get filter form
    filter_form = RetrievalFilterForm(request.GET)

    # Base queryset
    requests = RetrievalRequest.objects.filter(
        employee=user
    ).select_related(
        'supervisor',
        'content_type',
        'rejected_by'
    ).order_by('-submitted_at')

    # Apply filters
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        action_type = filter_form.cleaned_data.get('action_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')

        if status:
            requests = requests.filter(status=status)

        if action_type:
            requests = requests.filter(action_type=action_type)

        if date_from:
            requests = requests.filter(submitted_at__date__gte=date_from)

        if date_to:
            requests = requests.filter(submitted_at__date__lte=date_to)

        if search:
            requests = requests.filter(
                Q(reason__icontains=search) |
                Q(object_id__icontains=search)
            )

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Calculate statistics
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='PENDING').count(),
        'auto_approved': requests.filter(status='AUTO_APPROVED').count(),
        'approved': requests.filter(status='APPROVED').count(),
        'rejected': requests.filter(status='REJECTED').count(),
        'completed': requests.filter(status='COMPLETED').count(),
    }

    # Get accuracy metrics
    accuracy_metrics = {
        'month': RetrievalService.calculate_employee_accuracy(user, 'month'),
        'week': RetrievalService.calculate_employee_accuracy(user, 'week'),
    }

    context = {
        'page_obj': page_obj,
        'requests': page_obj.object_list,
        'filter_form': filter_form,
        'stats': stats,
        'accuracy_metrics': accuracy_metrics,
        'page_title': 'My Retrieval Requests'
    }

    return render(request, 'retrieval/dashboard.html', context)


@login_required
def create_retrieval_request(request, content_type_id, object_id):
    """
    Create a retrieval request for a specific object.

    Args:
        content_type_id: ID of the ContentType
        object_id: ID of the object to retrieve

    Shows:
    - Warning if outside time window
    - Dependency information
    - Request form
    """
    content_type = get_object_or_404(ContentType, id=content_type_id)
    model_class = content_type.model_class()

    try:
        obj = model_class.objects.get(pk=object_id)
    except model_class.DoesNotExist:
        messages.error(request, 'Object not found.')
        return redirect('retrieval:dashboard')

    # Check if object has retrieval capability
    if not hasattr(obj, 'can_be_retrieved'):
        messages.error(request, 'This object does not support retrieval.')
        return redirect('retrieval:dashboard')

    # Check if can be retrieved
    can_retrieve, reasons = obj.can_be_retrieved()

    if request.method == 'POST':
        form = RetrievalRequestForm(request.POST)

        if form.is_valid():
            try:
                # Create retrieval request using the mixin method
                retrieval_request = obj.create_retrieval_request(
                    employee=request.user,
                    reason=form.cleaned_data['reason'],
                    action_type=form.cleaned_data['action_type'],
                    auto_check=True
                )

                if retrieval_request.status == 'AUTO_APPROVED':
                    messages.success(
                        request,
                        'Your retrieval request has been automatically approved! '
                        'You can now proceed with the retrieval.'
                    )
                else:
                    messages.success(
                        request,
                        'Your retrieval request has been submitted and your supervisor has been notified. '
                        'You will be notified once it is reviewed.'
                    )

                return redirect('retrieval:request_detail', pk=retrieval_request.id)

            except Exception as e:
                messages.error(request, f'Error creating retrieval request: {str(e)}')
    else:
        form = RetrievalRequestForm()

    # Get dependencies
    dependencies = RetrievalService.check_dependencies(obj)

    context = {
        'form': form,
        'object': obj,
        'content_type': content_type,
        'can_retrieve': can_retrieve,
        'reasons': reasons,
        'dependencies': dependencies,
        'page_title': f'Request Retrieval - {obj}'
    }

    return render(request, 'retrieval/request_form.html', context)


@login_required
def request_detail(request, pk):
    """
    Display details of a retrieval request.
    """
    retrieval_request = get_object_or_404(
        RetrievalRequest.objects.select_related(
            'employee',
            'supervisor',
            'content_type',
            'rejected_by'
        ),
        pk=pk
    )

    # Check permissions
    if not (request.user == retrieval_request.employee or
            request.user == retrieval_request.supervisor or
            request.user.is_staff):
        raise Http404("You don't have permission to view this request.")

    context = {
        'request_obj': retrieval_request,
        'page_title': f'Retrieval Request #{retrieval_request.id}'
    }

    return render(request, 'retrieval/request_detail.html', context)


@login_required
def supervisor_dashboard(request):
    """
    Supervisor dashboard for reviewing pending retrieval requests.

    Shows:
    - Pending retrieval requests awaiting supervisor approval
    - Employee details and history
    - Original data preview
    - Approve/Reject actions
    - Employee accuracy metrics
    """
    user = request.user

    # Get filter form
    filter_form = RetrievalFilterForm(request.GET)

    # Base queryset - requests where user is supervisor
    requests = RetrievalRequest.objects.filter(
        supervisor=user
    ).select_related(
        'employee',
        'content_type'
    ).order_by('-submitted_at')

    # Apply filters
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        action_type = filter_form.cleaned_data.get('action_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')

        if status:
            requests = requests.filter(status=status)

        if action_type:
            requests = requests.filter(action_type=action_type)

        if date_from:
            requests = requests.filter(submitted_at__date__gte=date_from)

        if date_to:
            requests = requests.filter(submitted_at__date__lte=date_to)

        if search:
            requests = requests.filter(
                Q(reason__icontains=search) |
                Q(employee__username__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search)
            )

    # Separate pending from others
    pending_requests = requests.filter(status='PENDING')
    other_requests = requests.exclude(status='PENDING')

    # Pagination for pending
    pending_paginator = Paginator(pending_requests, 10)
    pending_page = request.GET.get('pending_page', 1)
    pending_page_obj = pending_paginator.get_page(pending_page)

    # Pagination for history
    history_paginator = Paginator(other_requests, 20)
    history_page = request.GET.get('history_page', 1)
    history_page_obj = history_paginator.get_page(history_page)

    # Calculate statistics
    stats = {
        'pending': pending_requests.count(),
        'approved': requests.filter(status__in=['APPROVED', 'AUTO_APPROVED']).count(),
        'rejected': requests.filter(status='REJECTED').count(),
        'completed': requests.filter(status='COMPLETED').count(),
    }

    # Get employee metrics for pending requests
    employee_metrics = {}
    for req in pending_page_obj.object_list:
        if req.employee.id not in employee_metrics:
            employee_metrics[req.employee.id] = RetrievalService.calculate_employee_accuracy(
                req.employee,
                'month'
            )

    context = {
        'pending_page_obj': pending_page_obj,
        'history_page_obj': history_page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'employee_metrics': employee_metrics,
        'page_title': 'Supervisor - Retrieval Approvals'
    }

    return render(request, 'retrieval/supervisor_dashboard.html', context)


@login_required
def approve_retrieval(request, pk):
    """
    Approve a retrieval request.
    """
    retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

    # Check permissions
    if request.user != retrieval_request.supervisor and not request.user.is_staff:
        messages.error(request, "You don't have permission to approve this request.")
        return redirect('retrieval:supervisor_dashboard')

    if retrieval_request.status != 'PENDING':
        messages.warning(request, "This request has already been processed.")
        return redirect('retrieval:supervisor_dashboard')

    if request.method == 'POST':
        form = SupervisorApprovalForm(request.POST)

        if form.is_valid():
            decision = form.cleaned_data['decision']

            if decision == 'approve':
                retrieval_request.approve(approved_by=request.user, auto=False)
                messages.success(
                    request,
                    f'Retrieval request #{retrieval_request.id} has been approved. '
                    f'Employee {retrieval_request.employee.get_full_name() or retrieval_request.employee.username} '
                    f'has been notified.'
                )
                RetrievalService.notify_employee_decision(retrieval_request)

            elif decision == 'reject':
                rejection_reason = form.cleaned_data['rejection_reason']
                retrieval_request.reject(
                    rejected_by=request.user,
                    reason=rejection_reason
                )
                messages.info(
                    request,
                    f'Retrieval request #{retrieval_request.id} has been rejected. '
                    f'Employee has been notified.'
                )
                RetrievalService.notify_employee_decision(retrieval_request)

            return redirect('retrieval:supervisor_dashboard')
    else:
        form = SupervisorApprovalForm()

    # Get employee metrics
    employee_metrics = RetrievalService.calculate_employee_accuracy(
        retrieval_request.employee,
        'month'
    )

    context = {
        'form': form,
        'request_obj': retrieval_request,
        'employee_metrics': employee_metrics,
        'page_title': f'Review Retrieval Request #{retrieval_request.id}'
    }

    return render(request, 'retrieval/approve_request.html', context)


@login_required
def reject_retrieval(request, pk):
    """
    Reject a retrieval request (quick action).
    """
    retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

    # Check permissions
    if request.user != retrieval_request.supervisor and not request.user.is_staff:
        messages.error(request, "You don't have permission to reject this request.")
        return redirect('retrieval:supervisor_dashboard')

    if retrieval_request.status != 'PENDING':
        messages.warning(request, "This request has already been processed.")
        return redirect('retrieval:supervisor_dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Rejection reason is required.')
        else:
            retrieval_request.reject(
                rejected_by=request.user,
                reason=reason
            )
            messages.info(
                request,
                f'Retrieval request #{retrieval_request.id} has been rejected. '
                f'Employee has been notified.'
            )
            RetrievalService.notify_employee_decision(retrieval_request)
            return redirect('retrieval:supervisor_dashboard')

    return redirect('retrieval:approve_retrieval', pk=pk)


@login_required
def complete_retrieval(request, pk):
    """
    Complete an approved retrieval request (execute the retrieval).
    """
    retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

    # Check permissions - only employee or staff can complete
    if request.user != retrieval_request.employee and not request.user.is_staff:
        messages.error(request, "You don't have permission to complete this request.")
        return redirect('retrieval:dashboard')

    if not retrieval_request.can_be_completed:
        messages.warning(request, "This request cannot be completed yet.")
        return redirect('retrieval:request_detail', pk=pk)

    if request.method == 'POST':
        try:
            # Get the object
            obj = retrieval_request.content_object

            if obj and hasattr(obj, 'perform_retrieval'):
                obj.perform_retrieval(retrieval_request)
                messages.success(
                    request,
                    f'Retrieval completed successfully for {retrieval_request.get_object_display()}.'
                )
            else:
                messages.error(request, 'Unable to complete retrieval - object not found or not retrievable.')

        except Exception as e:
            messages.error(request, f'Error completing retrieval: {str(e)}')

        return redirect('retrieval:request_detail', pk=pk)

    context = {
        'request_obj': retrieval_request,
        'page_title': f'Complete Retrieval #{retrieval_request.id}'
    }

    return render(request, 'retrieval/complete_retrieval.html', context)


@login_required
def cancel_retrieval(request, pk):
    """
    Cancel a pending retrieval request.
    """
    retrieval_request = get_object_or_404(RetrievalRequest, pk=pk)

    # Check permissions - only employee can cancel
    if request.user != retrieval_request.employee:
        messages.error(request, "You can only cancel your own requests.")
        return redirect('retrieval:dashboard')

    if retrieval_request.status != 'PENDING':
        messages.warning(request, "Only pending requests can be cancelled.")
        return redirect('retrieval:request_detail', pk=pk)

    if request.method == 'POST':
        retrieval_request.cancel()
        messages.info(request, f'Retrieval request #{retrieval_request.id} has been cancelled.')
        return redirect('retrieval:dashboard')

    context = {
        'request_obj': retrieval_request,
        'page_title': f'Cancel Retrieval Request #{retrieval_request.id}'
    }

    return render(request, 'retrieval/cancel_retrieval.html', context)


@login_required
def employee_metrics(request, employee_id=None):
    """
    Display detailed employee retrieval metrics.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if employee_id:
        # Check permissions - supervisor or staff can view others
        employee = get_object_or_404(User, pk=employee_id)
        if request.user != employee and not request.user.is_staff:
            # Check if user is supervisor
            if not RetrievalRequest.objects.filter(
                employee=employee,
                supervisor=request.user
            ).exists():
                raise Http404("You don't have permission to view these metrics.")
    else:
        employee = request.user

    # Get metrics for different periods
    metrics = {
        'day': RetrievalService.calculate_employee_accuracy(employee, 'day'),
        'week': RetrievalService.calculate_employee_accuracy(employee, 'week'),
        'month': RetrievalService.calculate_employee_accuracy(employee, 'month'),
        'quarter': RetrievalService.calculate_employee_accuracy(employee, 'quarter'),
        'year': RetrievalService.calculate_employee_accuracy(employee, 'year'),
    }

    # Get recent requests
    recent_requests = RetrievalRequest.objects.filter(
        employee=employee
    ).select_related('supervisor').order_by('-submitted_at')[:10]

    context = {
        'employee': employee,
        'metrics': metrics,
        'recent_requests': recent_requests,
        'page_title': f'Retrieval Metrics - {employee.get_full_name() or employee.username}'
    }

    return render(request, 'retrieval/employee_metrics.html', context)

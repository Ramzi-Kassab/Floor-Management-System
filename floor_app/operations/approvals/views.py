"""
Approval Workflow System Views

Template-rendering views for approval requests, workflows,
and approval management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import Http404

from .models import (
    ApprovalWorkflow,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStep,
    ApprovalHistory,
    ApprovalDelegation,
)


def is_staff_user(user):
    """Check if user is staff member."""
    return user.is_staff or user.is_superuser


@login_required
def pending_approvals(request):
    """
    Display pending approvals for the current user.

    Shows:
    - Approvals waiting for user's action
    - Delegated approvals
    - Overdue approvals
    - Statistics
    """
    user = request.user

    try:
        # Get pending approval steps for this user
        pending_steps = ApprovalStep.objects.filter(
            Q(approver=user) | Q(delegated_to=user),
            status='PENDING'
        ).select_related(
            'request',
            'request__workflow',
            'request__requester',
            'level'
        ).prefetch_related(
            'request__steps'
        ).order_by('-request__priority', 'due_at')

        # Separate by priority
        urgent_approvals = pending_steps.filter(request__priority='URGENT')
        high_approvals = pending_steps.filter(request__priority='HIGH')
        normal_approvals = pending_steps.filter(request__priority='NORMAL')

        # Statistics
        stats = {
            'total_pending': pending_steps.count(),
            'urgent': urgent_approvals.count(),
            'high': high_approvals.count(),
            'overdue': pending_steps.filter(is_overdue=True).count(),
        }

        # Recent activity - approvals I've taken action on
        recent_activity = ApprovalStep.objects.filter(
            approver=user,
            status__in=['APPROVED', 'REJECTED']
        ).select_related(
            'request',
            'request__workflow'
        ).order_by('-approved_at', '-rejected_at')[:10]

        context = {
            'pending_steps': pending_steps,
            'urgent_approvals': urgent_approvals,
            'high_approvals': high_approvals,
            'normal_approvals': normal_approvals,
            'stats': stats,
            'recent_activity': recent_activity,
            'page_title': 'Pending Approvals',
        }

    except Exception as e:
        messages.error(request, f'Error loading approvals: {str(e)}')
        context = {
            'pending_steps': [],
            'stats': {'total_pending': 0, 'urgent': 0, 'high': 0, 'overdue': 0},
            'page_title': 'Pending Approvals',
        }

    return render(request, 'approvals/pending_approvals.html', context)


@login_required
def request_detail(request, pk):
    """
    Display detailed view of an approval request.

    Shows:
    - Request details
    - Current status
    - Approval workflow progress
    - History/audit trail
    - Actions available to user
    """
    user = request.user

    try:
        approval_request = ApprovalRequest.objects.select_related(
            'workflow',
            'requester',
            'content_type'
        ).prefetch_related(
            'steps__approver',
            'steps__level',
            'history__action_by'
        ).get(pk=pk)

        # Check if user can see this request
        if not approval_request.can_user_see(user):
            messages.error(request, 'You do not have permission to view this approval request.')
            raise Http404('Approval request not found')

        # Handle approval/rejection
        if request.method == 'POST':
            action = request.POST.get('action')
            step_id = request.POST.get('step_id')
            comments = request.POST.get('comments', '')

            if step_id:
                try:
                    step = ApprovalStep.objects.get(
                        pk=step_id,
                        approver=user,
                        status='PENDING'
                    )

                    if action == 'approve':
                        step.approve(comments)
                        ApprovalHistory.objects.create(
                            request=approval_request,
                            step=step,
                            action_type='APPROVED',
                            action_by=user,
                            comments=comments
                        )
                        messages.success(request, 'Approval request approved successfully.')

                    elif action == 'reject':
                        step.reject(comments)
                        ApprovalHistory.objects.create(
                            request=approval_request,
                            step=step,
                            action_type='REJECTED',
                            action_by=user,
                            comments=comments
                        )
                        messages.success(request, 'Approval request rejected.')

                    elif action == 'delegate':
                        delegate_user_id = request.POST.get('delegate_to')
                        if delegate_user_id:
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            delegate_user = User.objects.get(pk=delegate_user_id)
                            step.delegate(delegate_user, comments)
                            ApprovalHistory.objects.create(
                                request=approval_request,
                                step=step,
                                action_type='DELEGATED',
                                action_by=user,
                                comments=f'Delegated to {delegate_user.username}: {comments}'
                            )
                            messages.success(request, f'Approval delegated to {delegate_user.username}.')

                    return redirect('approvals:request_detail', pk=pk)

                except ApprovalStep.DoesNotExist:
                    messages.error(request, 'Approval step not found or already processed.')
                except Exception as e:
                    messages.error(request, f'Error processing approval: {str(e)}')

        # Get user's pending step if any
        user_step = approval_request.steps.filter(
            Q(approver=user) | Q(delegated_to=user),
            status='PENDING'
        ).first()

        # Get approval history
        history = approval_request.history.select_related('action_by', 'step').all()

        # Get all levels and their status
        workflow_levels = approval_request.workflow.levels.all()

        context = {
            'approval_request': approval_request,
            'user_step': user_step,
            'history': history,
            'workflow_levels': workflow_levels,
            'can_approve': user_step is not None,
            'page_title': approval_request.title,
        }

    except ApprovalRequest.DoesNotExist:
        messages.error(request, 'Approval request not found.')
        raise Http404('Approval request not found')
    except Exception as e:
        messages.error(request, f'Error loading approval request: {str(e)}')
        return redirect('approvals:pending_approvals')

    return render(request, 'approvals/request_detail.html', context)


@login_required
def request_form(request):
    """
    Create new approval request.

    Allows users to:
    - Select workflow type
    - Fill in request details
    - Attach files
    - Submit for approval
    """
    workflows = ApprovalWorkflow.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        try:
            workflow_id = request.POST.get('workflow')
            title = request.POST.get('title')
            description = request.POST.get('description')
            priority = request.POST.get('priority', 'NORMAL')

            if not all([workflow_id, title, description]):
                messages.error(request, 'Please fill in all required fields.')
            else:
                workflow = get_object_or_404(ApprovalWorkflow, pk=workflow_id)

                # Create approval request
                approval_request = ApprovalRequest.objects.create(
                    workflow=workflow,
                    title=title,
                    description=description,
                    requester=request.user,
                    priority=priority,
                    status='DRAFT'
                )

                # Auto-submit if requested
                if request.POST.get('submit_now') == 'on':
                    approval_request.submit()
                    ApprovalHistory.objects.create(
                        request=approval_request,
                        action_type='SUBMITTED',
                        action_by=request.user
                    )
                    messages.success(request, 'Approval request submitted successfully.')
                else:
                    messages.success(request, 'Approval request created as draft.')

                return redirect('approvals:request_detail', pk=approval_request.pk)

        except Exception as e:
            messages.error(request, f'Error creating approval request: {str(e)}')

    context = {
        'workflows': workflows,
        'page_title': 'New Approval Request',
    }

    return render(request, 'approvals/request_form.html', context)


@login_required
def workflow_list(request):
    """
    Display list of approval workflows.

    Shows all available workflows and their configuration.
    """
    try:
        workflows = ApprovalWorkflow.objects.prefetch_related(
            'levels__approver_departments',
            'levels__approver_users'
        ).annotate(
            request_count=Count('requests')
        ).order_by('workflow_type')

        # Filter by active status
        filter_active = request.GET.get('active')
        if filter_active == 'true':
            workflows = workflows.filter(is_active=True)
        elif filter_active == 'false':
            workflows = workflows.filter(is_active=False)

        context = {
            'workflows': workflows,
            'filter_active': filter_active,
            'page_title': 'Approval Workflows',
        }

    except Exception as e:
        messages.error(request, f'Error loading workflows: {str(e)}')
        context = {
            'workflows': [],
            'page_title': 'Approval Workflows',
        }

    return render(request, 'approvals/workflow_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def workflow_designer(request):
    """
    Design and configure approval workflows (staff only).

    Allows staff to:
    - Create new workflows
    - Define approval levels
    - Set approvers
    - Configure escalation rules
    """
    if request.method == 'POST':
        try:
            workflow_id = request.POST.get('workflow_id')

            if workflow_id:
                # Edit existing workflow
                workflow = get_object_or_404(ApprovalWorkflow, pk=workflow_id)
                action = 'updated'
            else:
                # Create new workflow
                workflow = ApprovalWorkflow()
                action = 'created'

            # Update workflow fields
            workflow.workflow_type = request.POST.get('workflow_type')
            workflow.name = request.POST.get('name')
            workflow.description = request.POST.get('description', '')
            workflow.is_active = request.POST.get('is_active') == 'on'
            workflow.escalation_enabled = request.POST.get('escalation_enabled') == 'on'
            workflow.escalation_hours = int(request.POST.get('escalation_hours', 24))
            workflow.notify_requester_on_approval = request.POST.get('notify_requester_on_approval') == 'on'
            workflow.notify_requester_on_rejection = request.POST.get('notify_requester_on_rejection') == 'on'

            workflow.save()
            messages.success(request, f'Workflow "{workflow.name}" {action} successfully.')
            return redirect('approvals:workflow_designer')

        except Exception as e:
            messages.error(request, f'Error saving workflow: {str(e)}')

    # Get all workflows
    workflows = ApprovalWorkflow.objects.prefetch_related('levels').all()

    # Get workflow type choices
    workflow_types = ApprovalWorkflow.WORKFLOW_TYPES

    context = {
        'workflows': workflows,
        'workflow_types': workflow_types,
        'page_title': 'Workflow Designer',
    }

    return render(request, 'approvals/workflow_designer.html', context)


@login_required
def history(request):
    """
    View approval history.

    Shows:
    - User's approval requests
    - Requests user has approved/rejected
    - Complete audit trail
    """
    user = request.user

    try:
        # Requests made by user
        my_requests = ApprovalRequest.objects.filter(
            requester=user
        ).select_related(
            'workflow'
        ).prefetch_related(
            'steps'
        ).order_by('-created_at')

        # Requests user has acted on
        acted_on = ApprovalStep.objects.filter(
            approver=user,
            status__in=['APPROVED', 'REJECTED']
        ).select_related(
            'request',
            'request__workflow'
        ).order_by('-approved_at', '-rejected_at')

        # Filter by status
        filter_status = request.GET.get('status')
        if filter_status:
            my_requests = my_requests.filter(status=filter_status)

        # Filter by date range
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if from_date:
            my_requests = my_requests.filter(created_at__gte=from_date)
            acted_on = acted_on.filter(request__created_at__gte=from_date)

        if to_date:
            my_requests = my_requests.filter(created_at__lte=to_date)
            acted_on = acted_on.filter(request__created_at__lte=to_date)

        # Statistics
        stats = {
            'total_submitted': ApprovalRequest.objects.filter(requester=user).count(),
            'approved': ApprovalRequest.objects.filter(requester=user, status='APPROVED').count(),
            'rejected': ApprovalRequest.objects.filter(requester=user, status='REJECTED').count(),
            'pending': ApprovalRequest.objects.filter(requester=user, status__in=['SUBMITTED', 'IN_PROGRESS']).count(),
            'total_acted': acted_on.count(),
        }

        context = {
            'my_requests': my_requests,
            'acted_on': acted_on,
            'stats': stats,
            'filter_status': filter_status,
            'page_title': 'Approval History',
        }

    except Exception as e:
        messages.error(request, f'Error loading history: {str(e)}')
        context = {
            'my_requests': [],
            'acted_on': [],
            'stats': {},
            'page_title': 'Approval History',
        }

    return render(request, 'approvals/history.html', context)


@login_required
def delegation_manage(request):
    """
    Manage approval delegations.

    Allows users to:
    - Delegate approvals to others
    - View active delegations
    - Remove delegations
    """
    user = request.user

    try:
        # Get user's delegations (as delegator)
        my_delegations = ApprovalDelegation.objects.filter(
            delegator=user
        ).select_related('delegate').order_by('-start_date')

        # Get delegations to user (as delegate)
        delegations_to_me = ApprovalDelegation.objects.filter(
            delegate=user
        ).select_related('delegator').order_by('-start_date')

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'create':
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()

                    delegate_id = request.POST.get('delegate')
                    start_date = request.POST.get('start_date')
                    end_date = request.POST.get('end_date')
                    reason = request.POST.get('reason', '')

                    if all([delegate_id, start_date, end_date]):
                        delegate_user = User.objects.get(pk=delegate_id)

                        ApprovalDelegation.objects.create(
                            delegator=user,
                            delegate=delegate_user,
                            start_date=start_date,
                            end_date=end_date,
                            reason=reason,
                            is_active=True
                        )

                        messages.success(request, f'Delegation to {delegate_user.username} created successfully.')
                    else:
                        messages.error(request, 'Please fill in all required fields.')

                except Exception as e:
                    messages.error(request, f'Error creating delegation: {str(e)}')

            elif action == 'deactivate':
                delegation_id = request.POST.get('delegation_id')
                if delegation_id:
                    try:
                        delegation = ApprovalDelegation.objects.get(
                            pk=delegation_id,
                            delegator=user
                        )
                        delegation.is_active = False
                        delegation.save()
                        messages.success(request, 'Delegation deactivated successfully.')
                    except ApprovalDelegation.DoesNotExist:
                        messages.error(request, 'Delegation not found.')

            return redirect('approvals:delegation_manage')

        # Get available users for delegation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        available_users = User.objects.filter(is_active=True).exclude(pk=user.pk).order_by('username')

        context = {
            'my_delegations': my_delegations,
            'delegations_to_me': delegations_to_me,
            'available_users': available_users,
            'page_title': 'Delegation Management',
        }

    except Exception as e:
        messages.error(request, f'Error loading delegations: {str(e)}')
        context = {
            'my_delegations': [],
            'delegations_to_me': [],
            'available_users': [],
            'page_title': 'Delegation Management',
        }

    return render(request, 'approvals/delegation_manage.html', context)

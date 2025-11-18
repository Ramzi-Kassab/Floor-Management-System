"""
Workflow Automation Engine for Floor Management System.

Features:
- Approval workflows
- State machines
- Automatic transitions
- Business rules engine
- Workflow notifications
- Task assignments
"""

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction

from .notification_utils import create_notification, log_activity

User = get_user_model()


class WorkflowState:
    """
    Workflow state definition.

    Attributes:
        name: State name
        label: Human-readable label
        is_initial: Whether this is initial state
        is_final: Whether this is a final state
        allowed_transitions: List of states this can transition to
        required_permissions: Permissions required to enter this state
        auto_transitions: Dict of conditions to states for automatic transitions
    """

    def __init__(self, name, label, is_initial=False, is_final=False,
                 allowed_transitions=None, required_permissions=None,
                 auto_transitions=None):
        self.name = name
        self.label = label
        self.is_initial = is_initial
        self.is_final = is_final
        self.allowed_transitions = allowed_transitions or []
        self.required_permissions = required_permissions or []
        self.auto_transitions = auto_transitions or {}

    def can_transition_to(self, target_state, user=None):
        """Check if can transition to target state."""
        if target_state not in self.allowed_transitions:
            return False

        if user and self.required_permissions:
            return user.has_perms(self.required_permissions)

        return True


class WorkflowEngine:
    """
    Workflow state machine engine.

    Manages state transitions, validations, and notifications.
    """

    def __init__(self, states=None):
        """
        Initialize workflow engine.

        Args:
            states: List of WorkflowState objects
        """
        self.states = {s.name: s for s in (states or [])}

    def get_state(self, state_name):
        """Get state object by name."""
        return self.states.get(state_name)

    def get_initial_state(self):
        """Get initial state."""
        for state in self.states.values():
            if state.is_initial:
                return state
        return None

    def can_transition(self, from_state, to_state, user=None):
        """Check if transition is allowed."""
        state = self.get_state(from_state)
        if not state:
            return False

        return state.can_transition_to(to_state, user)

    def transition(self, obj, to_state, user=None, comment=None, notify=True):
        """
        Perform state transition.

        Args:
            obj: Object to transition
            to_state: Target state name
            user: User performing transition
            comment: Optional comment
            notify: Whether to send notifications

        Returns:
            bool: Success status
        """
        if not hasattr(obj, 'workflow_state'):
            return False

        current_state = obj.workflow_state

        # Validate transition
        if not self.can_transition(current_state, to_state, user):
            return False

        # Perform transition
        old_state = obj.workflow_state
        obj.workflow_state = to_state
        obj.save(update_fields=['workflow_state'])

        # Log transition
        if user:
            log_activity(
                user=user,
                action='WORKFLOW_TRANSITION',
                description=f'Transitioned {obj} from {old_state} to {to_state}',
                related_object=obj,
                extra_data={
                    'old_state': old_state,
                    'new_state': to_state,
                    'comment': comment
                }
            )

        # Send notifications
        if notify:
            self._send_transition_notifications(obj, old_state, to_state, user)

        # Check for auto-transitions
        self._check_auto_transitions(obj)

        return True

    def _send_transition_notifications(self, obj, old_state, new_state, user):
        """Send notifications for state transition."""
        # This can be customized per workflow
        pass

    def _check_auto_transitions(self, obj):
        """Check and execute automatic transitions."""
        state = self.get_state(obj.workflow_state)

        if not state or not state.auto_transitions:
            return

        for condition, target_state in state.auto_transitions.items():
            if self._evaluate_condition(obj, condition):
                self.transition(obj, target_state, notify=False)
                break

    def _evaluate_condition(self, obj, condition):
        """Evaluate a condition for auto-transition."""
        # Simple condition evaluation
        # Can be extended to support complex conditions
        if callable(condition):
            return condition(obj)

        return False


class ApprovalWorkflow:
    """
    Multi-level approval workflow.

    Features:
    - Multiple approval levels
    - Parallel or sequential approvals
    - Automatic approver assignment
    - Approval notifications
    - Approval history
    """

    def __init__(self, approval_levels=None):
        """
        Initialize approval workflow.

        Args:
            approval_levels: List of approval level definitions
                [
                    {'name': 'Manager', 'approvers': [user1, user2], 'required': 1},
                    {'name': 'Director', 'approvers': [user3], 'required': 1},
                ]
        """
        self.approval_levels = approval_levels or []

    def submit_for_approval(self, obj, submitted_by, comment=None):
        """
        Submit object for approval.

        Args:
            obj: Object to approve
            submitted_by: User submitting
            comment: Optional submission comment

        Returns:
            dict: Approval request details
        """
        # Create approval request tracking
        approval_data = {
            'submitted_by': submitted_by.id,
            'submitted_at': timezone.now().isoformat(),
            'current_level': 0,
            'status': 'PENDING',
            'levels': []
        }

        for level in self.approval_levels:
            approval_data['levels'].append({
                'name': level['name'],
                'required_approvals': level['required'],
                'approvers': [u.id for u in level['approvers']],
                'approvals': [],
                'status': 'PENDING'
            })

        # Store in object (assuming it has approval_data field)
        if hasattr(obj, 'approval_data'):
            obj.approval_data = approval_data
            obj.save(update_fields=['approval_data'])

        # Notify first level approvers
        self._notify_approvers(obj, 0)

        # Log activity
        log_activity(
            user=submitted_by,
            action='APPROVAL_SUBMITTED',
            description=f'Submitted {obj} for approval',
            related_object=obj,
            extra_data={'comment': comment}
        )

        return approval_data

    def approve(self, obj, user, comment=None):
        """
        Approve at current level.

        Args:
            obj: Object being approved
            user: User approving
            comment: Optional approval comment

        Returns:
            dict: Updated approval status
        """
        if not hasattr(obj, 'approval_data'):
            return None

        approval_data = obj.approval_data
        current_level = approval_data['current_level']

        if current_level >= len(approval_data['levels']):
            return None  # All levels complete

        level = approval_data['levels'][current_level]

        # Check if user is approver for this level
        if user.id not in level['approvers']:
            return None

        # Check if user already approved
        if user.id in [a['user_id'] for a in level['approvals']]:
            return None

        # Add approval
        level['approvals'].append({
            'user_id': user.id,
            'approved_at': timezone.now().isoformat(),
            'comment': comment
        })

        # Check if level is complete
        if len(level['approvals']) >= level['required_approvals']:
            level['status'] = 'APPROVED'

            # Move to next level or complete
            if current_level + 1 < len(approval_data['levels']):
                approval_data['current_level'] += 1
                self._notify_approvers(obj, current_level + 1)
            else:
                # All levels approved
                approval_data['status'] = 'APPROVED'
                self._on_fully_approved(obj, user)

        # Save changes
        obj.approval_data = approval_data
        obj.save(update_fields=['approval_data'])

        # Log activity
        log_activity(
            user=user,
            action='APPROVAL_APPROVED',
            description=f'Approved {obj} at level {level["name"]}',
            related_object=obj,
            extra_data={'level': current_level, 'comment': comment}
        )

        return approval_data

    def reject(self, obj, user, reason):
        """
        Reject approval request.

        Args:
            obj: Object being rejected
            user: User rejecting
            reason: Rejection reason

        Returns:
            dict: Updated approval status
        """
        if not hasattr(obj, 'approval_data'):
            return None

        approval_data = obj.approval_data
        approval_data['status'] = 'REJECTED'
        approval_data['rejected_by'] = user.id
        approval_data['rejected_at'] = timezone.now().isoformat()
        approval_data['rejection_reason'] = reason

        obj.approval_data = approval_data
        obj.save(update_fields=['approval_data'])

        # Notify submitter
        submitter = User.objects.get(id=approval_data['submitted_by'])
        create_notification(
            user=submitter,
            title='Approval Request Rejected',
            message=f'Your request for {obj} was rejected. Reason: {reason}',
            notification_type='WARNING',
            priority='HIGH',
            related_object=obj,
            created_by=user
        )

        # Log activity
        log_activity(
            user=user,
            action='APPROVAL_REJECTED',
            description=f'Rejected {obj}',
            related_object=obj,
            extra_data={'reason': reason}
        )

        return approval_data

    def _notify_approvers(self, obj, level_index):
        """Notify approvers at specified level."""
        if not hasattr(obj, 'approval_data'):
            return

        approval_data = obj.approval_data
        if level_index >= len(approval_data['levels']):
            return

        level = approval_data['levels'][level_index]
        approvers = User.objects.filter(id__in=level['approvers'])

        for approver in approvers:
            create_notification(
                user=approver,
                title='Approval Required',
                message=f'Your approval is required for {obj} at level {level["name"]}',
                notification_type='APPROVAL',
                priority='HIGH',
                related_object=obj
            )

    def _on_fully_approved(self, obj, final_approver):
        """Handle fully approved workflow."""
        # Notify submitter
        if hasattr(obj, 'approval_data'):
            submitter = User.objects.get(id=obj.approval_data['submitted_by'])
            create_notification(
                user=submitter,
                title='Approval Complete',
                message=f'Your request for {obj} has been fully approved',
                notification_type='SUCCESS',
                priority='NORMAL',
                related_object=obj
            )


class BusinessRule:
    """
    Business rule definition and execution.

    Features:
    - Condition-based rule execution
    - Multiple actions per rule
    - Rule prioritization
    """

    def __init__(self, name, condition, actions, priority=0, active=True):
        """
        Initialize business rule.

        Args:
            name: Rule name
            condition: Function that returns True/False
            actions: List of functions to execute if condition is True
            priority: Rule priority (higher = earlier execution)
            active: Whether rule is active
        """
        self.name = name
        self.condition = condition
        self.actions = actions if isinstance(actions, list) else [actions]
        self.priority = priority
        self.active = active

    def evaluate(self, context):
        """
        Evaluate rule condition.

        Args:
            context: Dict with data for evaluation

        Returns:
            bool: Whether condition is met
        """
        if not self.active:
            return False

        try:
            return self.condition(context)
        except Exception:
            return False

    def execute(self, context):
        """
        Execute rule actions.

        Args:
            context: Dict with data for actions

        Returns:
            list: Results of each action
        """
        results = []

        for action in self.actions:
            try:
                result = action(context)
                results.append({'success': True, 'result': result})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})

        return results


class BusinessRulesEngine:
    """
    Business rules engine.

    Manages and executes business rules.
    """

    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        """Add a rule to the engine."""
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_name):
        """Remove a rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def evaluate_all(self, context):
        """
        Evaluate all rules and return matching rules.

        Args:
            context: Dict with data for evaluation

        Returns:
            list: Rules that match conditions
        """
        matching_rules = []

        for rule in self.rules:
            if rule.evaluate(context):
                matching_rules.append(rule)

        return matching_rules

    def execute_all(self, context, stop_on_first=False):
        """
        Execute all matching rules.

        Args:
            context: Dict with data for execution
            stop_on_first: Stop after first matching rule

        Returns:
            list: Execution results
        """
        results = []

        for rule in self.rules:
            if rule.evaluate(context):
                rule_results = rule.execute(context)
                results.append({
                    'rule': rule.name,
                    'actions': rule_results
                })

                if stop_on_first:
                    break

        return results

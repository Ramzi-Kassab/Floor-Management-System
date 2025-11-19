"""
Retrieval System Mixins

Provides retrieval/undo capability to any model through RetrievableMixin.
"""

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from datetime import timedelta
import json


class RetrievableMixin:
    """
    Mixin to add retrieval/undo capability to any model.

    Usage:
        class MyModel(RetrievableMixin, models.Model):
            # your fields here
            pass

        # Check if object can be retrieved
        can_retrieve, reason = obj.can_be_retrieved()

        # Create retrieval request
        request = obj.create_retrieval_request(
            employee=user,
            reason="Made a mistake in data entry",
            action_type='DELETE'
        )

        # Perform retrieval (after approval)
        obj.perform_retrieval(request)
    """

    RETRIEVAL_TIME_WINDOW_MINUTES = 15  # Override in subclass if needed

    def can_be_retrieved(self, time_window_minutes=None):
        """
        Check if this record can be retrieved (undone).

        Checks:
        1. Time window (default 15 minutes since creation)
        2. Dependent processes (foreign key references)
        3. Object state (not already deleted, etc.)

        Args:
            time_window_minutes: Time window in minutes (uses class default if not provided)

        Returns:
            tuple: (can_retrieve: bool, reasons: list)
        """
        if time_window_minutes is None:
            time_window_minutes = getattr(self, 'RETRIEVAL_TIME_WINDOW_MINUTES', 15)

        reasons = []
        can_retrieve = True

        # Check 1: Time window
        if hasattr(self, 'created_at'):
            time_elapsed = timezone.now() - self.created_at
            time_window = timedelta(minutes=time_window_minutes)

            if time_elapsed > time_window:
                can_retrieve = False
                reasons.append(
                    f"Outside time window: {int(time_elapsed.total_seconds() / 60)} minutes elapsed "
                    f"(limit: {time_window_minutes} minutes)"
                )
        else:
            reasons.append("Warning: No created_at field to check time window")

        # Check 2: Dependent processes (foreign key references)
        dependencies = self._check_dependencies()
        if dependencies:
            can_retrieve = False
            reasons.append(f"Has {len(dependencies)} dependent process(es)")
            for dep in dependencies[:5]:  # Show first 5
                reasons.append(f"  - {dep['model']}: {dep['count']} record(s)")

        # Check 3: Soft delete status (if applicable)
        if hasattr(self, 'is_deleted') and self.is_deleted:
            reasons.append("Warning: Record is already soft-deleted")

        # Check 4: Check if already has pending retrieval request
        if self._has_pending_retrieval():
            can_retrieve = False
            reasons.append("Already has a pending retrieval request")

        if can_retrieve and not reasons:
            reasons.append("All checks passed - retrieval allowed")

        return can_retrieve, reasons

    def _check_dependencies(self):
        """
        Check for foreign key references (dependent processes).

        Returns:
            list: List of dependency dictionaries with model name and count
        """
        dependencies = []

        # Get all related objects using Django's _meta API
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()

            try:
                related_manager = getattr(self, related_name)
                count = related_manager.count()

                if count > 0:
                    dependencies.append({
                        'model': related_object.related_model.__name__,
                        'field': related_name,
                        'count': count,
                        'description': f"{count} {related_object.related_model._meta.verbose_name_plural}"
                    })
            except AttributeError:
                # Some related objects might not be accessible
                continue

        return dependencies

    def _has_pending_retrieval(self):
        """
        Check if this object already has a pending retrieval request.

        Returns:
            bool: True if pending request exists
        """
        from .models import RetrievalRequest

        content_type = ContentType.objects.get_for_model(self)
        pending_requests = RetrievalRequest.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            status='PENDING'
        )

        return pending_requests.exists()

    def create_retrieval_request(self, employee, reason, action_type='UNDO', auto_check=True):
        """
        Create a retrieval request for this object.

        This will:
        1. Snapshot the current object data
        2. Calculate time elapsed
        3. Check dependencies
        4. Determine if auto-approval is possible
        5. Get employee's supervisor
        6. Create the RetrievalRequest
        7. Send notification to supervisor

        Args:
            employee: User requesting the retrieval
            reason: Reason for retrieval
            action_type: Type of retrieval ('DELETE', 'EDIT', 'UNDO', 'RESTORE')
            auto_check: Whether to automatically check and approve if within time window

        Returns:
            RetrievalRequest: The created request object

        Raises:
            ValidationError: If retrieval is not allowed
        """
        from .models import RetrievalRequest
        from .services import RetrievalService

        # Check if retrieval is allowed
        can_retrieve, reasons = self.can_be_retrieved()

        # Create snapshot of original data
        original_data = self._create_data_snapshot()

        # Calculate time elapsed
        if hasattr(self, 'created_at'):
            time_elapsed = timezone.now() - self.created_at
        else:
            time_elapsed = timedelta(0)

        # Check dependencies
        dependencies = self._check_dependencies()
        has_dependencies = len(dependencies) > 0

        # Get employee's supervisor
        supervisor = self._get_supervisor(employee)

        # Create the retrieval request
        content_type = ContentType.objects.get_for_model(self)

        request = RetrievalRequest.objects.create(
            employee=employee,
            supervisor=supervisor,
            content_type=content_type,
            object_id=self.pk,
            action_type=action_type,
            reason=reason,
            original_data=original_data,
            status='PENDING',
            time_elapsed=time_elapsed,
            has_dependent_processes=has_dependencies,
            dependent_process_details={'dependencies': dependencies, 'reasons': reasons},
            created_by=employee
        )

        # Check if can be auto-approved
        if auto_check:
            can_auto, auto_reason = request.can_auto_approve()
            if can_auto:
                request.approve(approved_by=None, auto=True)

        # Send notification to supervisor
        if supervisor and request.status == 'PENDING':
            RetrievalService.notify_supervisor(request)

        return request

    def perform_retrieval(self, retrieval_request):
        """
        Execute the retrieval/undo action.

        This should be called after the retrieval request has been approved.

        Args:
            retrieval_request: Approved RetrievalRequest object

        Raises:
            ValidationError: If request is not approved or already completed
        """
        if not retrieval_request.is_approved:
            raise ValidationError("Retrieval request must be approved before execution")

        if retrieval_request.is_completed:
            raise ValidationError("Retrieval request already completed")

        # Perform the action based on action_type
        action_type = retrieval_request.action_type

        if action_type == 'DELETE':
            # Soft delete the object
            if hasattr(self, 'delete'):
                self.delete()
        elif action_type == 'RESTORE':
            # Restore soft-deleted object
            if hasattr(self, 'restore'):
                self.restore()
        elif action_type == 'EDIT':
            # Restore from snapshot
            self._restore_from_snapshot(retrieval_request.original_data)
        elif action_type == 'UNDO':
            # Generic undo - delete or soft delete
            if hasattr(self, 'is_deleted'):
                self.is_deleted = True
                self.deleted_at = timezone.now()
                self.save()
            else:
                self.delete()

        # Mark request as completed
        retrieval_request.complete()

        # Log the retrieval action
        self._log_retrieval_action(retrieval_request)

    def _create_data_snapshot(self):
        """
        Create a JSON snapshot of the current object data.

        Returns:
            dict: Serializable dictionary of object data
        """
        snapshot = {}

        for field in self._meta.fields:
            field_name = field.name
            field_value = getattr(self, field_name, None)

            # Convert to JSON-serializable format
            if isinstance(field_value, models.Model):
                snapshot[field_name] = {
                    'type': 'ForeignKey',
                    'model': field_value._meta.label,
                    'pk': field_value.pk,
                    'str': str(field_value)
                }
            elif hasattr(field_value, 'isoformat'):  # datetime, date, time
                snapshot[field_name] = field_value.isoformat()
            elif field_value is None:
                snapshot[field_name] = None
            else:
                try:
                    # Try to serialize as JSON
                    json.dumps(field_value)
                    snapshot[field_name] = field_value
                except (TypeError, ValueError):
                    # If not serializable, convert to string
                    snapshot[field_name] = str(field_value)

        return snapshot

    def _restore_from_snapshot(self, snapshot):
        """
        Restore object data from a snapshot.

        Args:
            snapshot: Dictionary of field values
        """
        for field_name, field_value in snapshot.items():
            if hasattr(self, field_name):
                # Handle ForeignKey restoration
                if isinstance(field_value, dict) and field_value.get('type') == 'ForeignKey':
                    # This would require more complex logic to restore ForeignKeys
                    # For now, we skip ForeignKey restoration
                    continue

                setattr(self, field_name, field_value)

        self.save()

    def _get_supervisor(self, employee):
        """
        Get the supervisor for the given employee.

        Override this method to customize supervisor lookup logic.

        Args:
            employee: User object

        Returns:
            User: Supervisor user or None
        """
        # Try to get supervisor from employee profile
        if hasattr(employee, 'employee_profile'):
            profile = employee.employee_profile
            if hasattr(profile, 'supervisor'):
                return profile.supervisor

        # Try to get from HR Position
        if hasattr(employee, 'current_position'):
            position = employee.current_position
            if hasattr(position, 'reports_to'):
                return position.reports_to.employee if position.reports_to else None

        # Fallback: return a staff/admin user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(is_staff=True).first()

    def _log_retrieval_action(self, retrieval_request):
        """
        Log the retrieval action to the activity log.

        Args:
            retrieval_request: RetrievalRequest object
        """
        # Try to import and use ActivityLog if available
        try:
            from core.models import ActivityLog

            ActivityLog.objects.create(
                user=retrieval_request.employee,
                action='OTHER',
                description=f"Retrieval completed: {retrieval_request.action_type} on {self._meta.verbose_name}",
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                extra_data={
                    'retrieval_request_id': retrieval_request.id,
                    'action_type': retrieval_request.action_type,
                    'reason': retrieval_request.reason,
                    'status': retrieval_request.status
                }
            )
        except ImportError:
            # ActivityLog not available, skip logging
            pass

    def get_retrieval_requests(self):
        """
        Get all retrieval requests for this object.

        Returns:
            QuerySet: RetrievalRequest objects for this object
        """
        from .models import RetrievalRequest

        content_type = ContentType.objects.get_for_model(self)
        return RetrievalRequest.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).order_by('-submitted_at')

    def has_retrieval_requests(self):
        """
        Check if this object has any retrieval requests.

        Returns:
            bool: True if retrieval requests exist
        """
        return self.get_retrieval_requests().exists()

    def get_pending_retrieval_request(self):
        """
        Get pending retrieval request for this object.

        Returns:
            RetrievalRequest or None: Pending request if exists
        """
        return self.get_retrieval_requests().filter(status='PENDING').first()

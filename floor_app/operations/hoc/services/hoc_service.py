"""
HOC Service

Business logic for Hazard Observation Card system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.db import transaction
from floor_app.operations.hoc.models import (
    HazardCategory,
    HazardObservation,
    HOCPhoto,
    HOCComment,
    HOCStatusHistory,
    HOCNotificationSettings
)

User = get_user_model()


class HOCService:
    """Service for managing hazard observations."""

    @classmethod
    def generate_card_number(cls) -> str:
        """
        Generate unique HOC card number.
        Format: HOC-YYYY-NNNN
        """
        year = timezone.now().year
        prefix = f"HOC-{year}-"

        # Get last number for this year
        last_hoc = HazardObservation.objects.filter(
            card_number__startswith=prefix
        ).order_by('-card_number').first()

        if last_hoc:
            last_number = int(last_hoc.card_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_observation(cls, submitted_by: User, data: Dict[str, Any]) -> HazardObservation:
        """
        Create a new hazard observation.

        Args:
            submitted_by: User submitting the observation
            data: Observation data

        Returns:
            Created HazardObservation instance
        """
        # Generate card number
        card_number = cls.generate_card_number()

        # Create observation
        observation = HazardObservation.objects.create(
            card_number=card_number,
            submitted_by=submitted_by,
            category_id=data['category_id'],
            severity=data['severity'],
            title=data['title'],
            description=data['description'],
            location=data['location'],
            department=data.get('department', ''),
            building=data.get('building', ''),
            floor_level=data.get('floor_level', ''),
            gps_coordinates=data.get('gps_coordinates', ''),
            potential_consequence=data.get('potential_consequence', ''),
            people_at_risk=data.get('people_at_risk'),
            immediate_action_taken=data.get('immediate_action_taken', ''),
            area_isolated=data.get('area_isolated', False),
            work_stopped=data.get('work_stopped', False),
            is_repeat_observation=data.get('is_repeat_observation', False),
            related_incident=data.get('related_incident', ''),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {}),
            status='SUBMITTED'
        )

        # Send notifications
        cls._send_submission_notification(observation)

        return observation

    @classmethod
    @transaction.atomic
    def update_observation(cls, observation_id: int, user: User, data: Dict[str, Any]) -> HazardObservation:
        """Update an existing observation."""
        observation = HazardObservation.objects.get(id=observation_id)

        # Update fields
        for field, value in data.items():
            if hasattr(observation, field) and field not in ['card_number', 'submitted_by', 'submission_date']:
                setattr(observation, field, value)

        observation.save()
        return observation

    @classmethod
    @transaction.atomic
    def assign_observation(cls, observation_id: int, assigned_by: User,
                           assigned_to: User, due_date: date = None,
                           action_plan: str = '') -> HazardObservation:
        """
        Assign observation to a responsible person.

        Args:
            observation_id: Observation ID
            assigned_by: User doing the assignment
            assigned_to: User being assigned
            due_date: Target completion date
            action_plan: Corrective action plan

        Returns:
            Updated HazardObservation
        """
        observation = HazardObservation.objects.get(id=observation_id)

        # Update assignment
        old_status = observation.status
        observation.assigned_to = assigned_to
        observation.assigned_date = timezone.now()
        observation.due_date = due_date
        observation.corrective_action_plan = action_plan
        observation.status = 'ACTION_ASSIGNED'
        observation.save()

        # Record status change
        cls._record_status_change(observation, old_status, 'ACTION_ASSIGNED', assigned_by)

        # Send notification
        cls._send_assignment_notification(observation, assigned_to)

        return observation

    @classmethod
    @transaction.atomic
    def update_status(cls, observation_id: int, new_status: str,
                      user: User, reason: str = '') -> HazardObservation:
        """
        Update observation status.

        Args:
            observation_id: Observation ID
            new_status: New status
            user: User making the change
            reason: Reason for status change

        Returns:
            Updated HazardObservation
        """
        observation = HazardObservation.objects.get(id=observation_id)
        old_status = observation.status

        observation.status = new_status

        # Update related fields based on status
        if new_status == 'UNDER_REVIEW':
            observation.reviewed_by = user
            observation.reviewed_date = timezone.now()
        elif new_status == 'IN_PROGRESS':
            if not observation.assigned_date:
                observation.assigned_date = timezone.now()
        elif new_status == 'COMPLETED':
            observation.action_completed_date = timezone.now()
        elif new_status == 'VERIFIED':
            observation.verified_by = user
            observation.verified_date = timezone.now()
        elif new_status == 'CLOSED':
            observation.closed_by = user
            observation.closed_date = timezone.now()

        observation.save()

        # Record status change
        cls._record_status_change(observation, old_status, new_status, user, reason)

        # Send notifications
        cls._send_status_change_notification(observation, old_status, new_status)

        return observation

    @classmethod
    @transaction.atomic
    def add_corrective_action(cls, observation_id: int, user: User,
                              action_taken: str) -> HazardObservation:
        """Add corrective action details."""
        observation = HazardObservation.objects.get(id=observation_id)

        observation.corrective_action_taken = action_taken
        observation.action_completed_date = timezone.now()

        if observation.status in ['SUBMITTED', 'UNDER_REVIEW', 'ACTION_ASSIGNED', 'IN_PROGRESS']:
            old_status = observation.status
            observation.status = 'COMPLETED'
            cls._record_status_change(observation, old_status, 'COMPLETED', user)

        observation.save()

        # Notify submitter
        cls._send_completion_notification(observation)

        return observation

    @classmethod
    @transaction.atomic
    def verify_observation(cls, observation_id: int, verified_by: User,
                           is_verified: bool, comments: str = '') -> HazardObservation:
        """Verify that corrective action is effective."""
        observation = HazardObservation.objects.get(id=observation_id)

        observation.verified_by = verified_by
        observation.verified_date = timezone.now()
        observation.verification_comments = comments

        old_status = observation.status
        observation.status = 'VERIFIED' if is_verified else 'IN_PROGRESS'
        observation.save()

        cls._record_status_change(observation, old_status, observation.status, verified_by, comments)

        return observation

    @classmethod
    @transaction.atomic
    def close_observation(cls, observation_id: int, closed_by: User,
                          closure_comments: str = '', actual_cost: float = None) -> HazardObservation:
        """Close an observation."""
        observation = HazardObservation.objects.get(id=observation_id)

        old_status = observation.status
        observation.closed_by = closed_by
        observation.closed_date = timezone.now()
        observation.closure_comments = closure_comments
        observation.status = 'CLOSED'

        if actual_cost is not None:
            observation.actual_cost = actual_cost

        observation.save()

        cls._record_status_change(observation, old_status, 'CLOSED', closed_by, closure_comments)

        return observation

    @classmethod
    def add_photo(cls, observation_id: int, photo_file, photo_type: str,
                  caption: str, uploaded_by: User) -> HOCPhoto:
        """Add a photo to an observation."""
        observation = HazardObservation.objects.get(id=observation_id)

        photo = HOCPhoto.objects.create(
            observation=observation,
            photo_type=photo_type,
            photo=photo_file,
            caption=caption,
            uploaded_by=uploaded_by
        )

        # TODO: Generate thumbnail

        return photo

    @classmethod
    def add_comment(cls, observation_id: int, comment_text: str,
                    commented_by: User, is_internal: bool = False) -> HOCComment:
        """Add a comment to an observation."""
        observation = HazardObservation.objects.get(id=observation_id)

        comment = HOCComment.objects.create(
            observation=observation,
            comment=comment_text,
            commented_by=commented_by,
            is_internal=is_internal
        )

        # Send notification
        if not is_internal:
            cls._send_comment_notification(observation, comment)

        return comment

    @classmethod
    def get_observations_by_status(cls, status: str = None, user: User = None) -> List[HazardObservation]:
        """Get observations filtered by status and/or user."""
        query = HazardObservation.objects.all()

        if status:
            query = query.filter(status=status)

        if user:
            query = query.filter(
                Q(submitted_by=user) |
                Q(assigned_to=user) |
                Q(reviewed_by=user)
            )

        return list(query.select_related('category', 'submitted_by', 'assigned_to'))

    @classmethod
    def get_overdue_observations(cls, assigned_to: User = None) -> List[HazardObservation]:
        """Get overdue observations."""
        today = timezone.now().date()

        query = HazardObservation.objects.filter(
            due_date__lt=today,
            status__in=['SUBMITTED', 'UNDER_REVIEW', 'ACTION_ASSIGNED', 'IN_PROGRESS']
        )

        if assigned_to:
            query = query.filter(assigned_to=assigned_to)

        return list(query.select_related('category', 'submitted_by', 'assigned_to'))

    @classmethod
    def get_observations_due_soon(cls, days: int = 7, assigned_to: User = None) -> List[HazardObservation]:
        """Get observations due within specified days."""
        today = timezone.now().date()
        future_date = today + timedelta(days=days)

        query = HazardObservation.objects.filter(
            due_date__gte=today,
            due_date__lte=future_date,
            status__in=['SUBMITTED', 'UNDER_REVIEW', 'ACTION_ASSIGNED', 'IN_PROGRESS']
        )

        if assigned_to:
            query = query.filter(assigned_to=assigned_to)

        return list(query.select_related('category', 'submitted_by', 'assigned_to'))

    @classmethod
    def get_statistics(cls, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get HOC statistics."""
        query = HazardObservation.objects.all()

        if start_date:
            query = query.filter(submission_date__date__gte=start_date)
        if end_date:
            query = query.filter(submission_date__date__lte=end_date)

        stats = {
            'total': query.count(),
            'by_status': dict(query.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_severity': dict(query.values('severity').annotate(count=Count('id')).values_list('severity', 'count')),
            'by_category': list(query.values('category__name').annotate(count=Count('id'))),
            'overdue': HazardObservation.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=['SUBMITTED', 'UNDER_REVIEW', 'ACTION_ASSIGNED', 'IN_PROGRESS']
            ).count(),
            'completed_this_period': query.filter(status__in=['COMPLETED', 'VERIFIED', 'CLOSED']).count(),
            'average_days_to_close': query.filter(
                closed_date__isnull=False
            ).annotate(
                days=F('closed_date') - F('submission_date')
            ).aggregate(avg_days=Avg('days'))['avg_days'],
        }

        return stats

    @classmethod
    def get_user_statistics(cls, user: User) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        submitted = HazardObservation.objects.filter(submitted_by=user)
        assigned = HazardObservation.objects.filter(assigned_to=user)

        return {
            'submitted_total': submitted.count(),
            'submitted_open': submitted.exclude(status='CLOSED').count(),
            'assigned_total': assigned.count(),
            'assigned_open': assigned.exclude(status='CLOSED').count(),
            'assigned_overdue': assigned.filter(
                due_date__lt=timezone.now().date(),
                status__in=['ACTION_ASSIGNED', 'IN_PROGRESS']
            ).count(),
        }

    @classmethod
    def _record_status_change(cls, observation: HazardObservation, from_status: str,
                              to_status: str, changed_by: User, reason: str = ''):
        """Record status change in history."""
        HOCStatusHistory.objects.create(
            observation=observation,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            reason=reason
        )

    @classmethod
    def _send_submission_notification(cls, observation: HazardObservation):
        """Send notification when new HOC is submitted."""
        # TODO: Implement notification logic
        pass

    @classmethod
    def _send_assignment_notification(cls, observation: HazardObservation, assigned_to: User):
        """Send notification when HOC is assigned."""
        # TODO: Implement notification logic
        pass

    @classmethod
    def _send_status_change_notification(cls, observation: HazardObservation,
                                          old_status: str, new_status: str):
        """Send notification on status change."""
        # TODO: Implement notification logic
        pass

    @classmethod
    def _send_completion_notification(cls, observation: HazardObservation):
        """Send notification when corrective action is completed."""
        # TODO: Implement notification logic
        pass

    @classmethod
    def _send_comment_notification(cls, observation: HazardObservation, comment: HOCComment):
        """Send notification when comment is added."""
        # TODO: Implement notification logic
        pass

    @classmethod
    def search_observations(cls, query_text: str, filters: Dict[str, Any] = None) -> List[HazardObservation]:
        """
        Search observations by text and filters.

        Args:
            query_text: Search text
            filters: Additional filters (status, severity, category, etc.)

        Returns:
            List of matching observations
        """
        query = HazardObservation.objects.all()

        # Text search
        if query_text:
            query = query.filter(
                Q(card_number__icontains=query_text) |
                Q(title__icontains=query_text) |
                Q(description__icontains=query_text) |
                Q(location__icontains=query_text)
            )

        # Apply filters
        if filters:
            if 'status' in filters:
                query = query.filter(status=filters['status'])
            if 'severity' in filters:
                query = query.filter(severity=filters['severity'])
            if 'category' in filters:
                query = query.filter(category_id=filters['category'])
            if 'submitted_by' in filters:
                query = query.filter(submitted_by_id=filters['submitted_by'])
            if 'assigned_to' in filters:
                query = query.filter(assigned_to_id=filters['assigned_to'])
            if 'start_date' in filters:
                query = query.filter(submission_date__date__gte=filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(submission_date__date__lte=filters['end_date'])

        return list(query.select_related('category', 'submitted_by', 'assigned_to'))

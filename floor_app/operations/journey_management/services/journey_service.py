"""Journey Service - Business logic for journey management"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from floor_app.operations.journey_management.models import (
    JourneyPlan, JourneyWaypoint, JourneyCheckIn, JourneyDocument, JourneyStatusHistory
)

User = get_user_model()


class JourneyService:
    """Service for managing journeys."""

    @classmethod
    def generate_journey_number(cls) -> str:
        """Generate unique journey number. Format: JRN-YYYY-NNNN"""
        year = timezone.now().year
        prefix = f"JRN-{year}-"

        last_journey = JourneyPlan.objects.filter(
            journey_number__startswith=prefix
        ).order_by('-journey_number').first()

        if last_journey:
            last_number = int(last_journey.journey_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    @classmethod
    @transaction.atomic
    def create_journey(cls, traveler: User, data: Dict[str, Any]) -> JourneyPlan:
        """Create a new journey plan."""
        journey_number = cls.generate_journey_number()

        journey = JourneyPlan.objects.create(
            journey_number=journey_number,
            traveler=traveler,
            title=data['title'],
            description=data.get('description', ''),
            departure_location=data['departure_location'],
            destination=data['destination'],
            planned_departure_time=data['planned_departure_time'],
            planned_return_time=data['planned_return_time'],
            route_description=data.get('route_description', ''),
            estimated_distance_km=data.get('estimated_distance_km'),
            vehicle_type=data['vehicle_type'],
            vehicle_number=data.get('vehicle_number', ''),
            vehicle_details=data.get('vehicle_details', {}),
            risk_level=data.get('risk_level', 'LOW'),
            risk_assessment=data.get('risk_assessment', ''),
            hazards_identified=data.get('hazards_identified', []),
            mitigation_measures=data.get('mitigation_measures', ''),
            emergency_contact_name=data['emergency_contact_name'],
            emergency_contact_phone=data['emergency_contact_phone'],
            emergency_contact_relationship=data.get('emergency_contact_relationship', ''),
            medical_conditions=data.get('medical_conditions', ''),
            purpose_category=data.get('purpose_category', 'OTHER'),
            estimated_cost=data.get('estimated_cost'),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {}),
            status='DRAFT'
        )

        # Add companions if provided
        if 'companion_ids' in data:
            companions = User.objects.filter(id__in=data['companion_ids'])
            journey.companions.set(companions)

        return journey

    @classmethod
    @transaction.atomic
    def submit_for_approval(cls, journey_id: int, user: User) -> JourneyPlan:
        """Submit journey for approval."""
        journey = JourneyPlan.objects.get(id=journey_id, traveler=user)

        if journey.status != 'DRAFT':
            raise ValueError("Only draft journeys can be submitted for approval")

        old_status = journey.status
        journey.status = 'SUBMITTED'
        journey.submitted_date = timezone.now()
        journey.save()

        cls._record_status_change(journey, old_status, 'SUBMITTED', user)

        return journey

    @classmethod
    @transaction.atomic
    def approve_journey(cls, journey_id: int, approved_by: User, comments: str = '') -> JourneyPlan:
        """Approve a journey."""
        journey = JourneyPlan.objects.get(id=journey_id)

        if journey.status != 'SUBMITTED':
            raise ValueError("Only submitted journeys can be approved")

        old_status = journey.status
        journey.status = 'APPROVED'
        journey.approved_by = approved_by
        journey.approval_date = timezone.now()
        journey.approval_comments = comments
        journey.save()

        cls._record_status_change(journey, old_status, 'APPROVED', approved_by, comments)

        return journey

    @classmethod
    @transaction.atomic
    def reject_journey(cls, journey_id: int, rejected_by: User, reason: str) -> JourneyPlan:
        """Reject a journey."""
        journey = JourneyPlan.objects.get(id=journey_id)

        if journey.status != 'SUBMITTED':
            raise ValueError("Only submitted journeys can be rejected")

        old_status = journey.status
        journey.status = 'REJECTED'
        journey.approved_by = rejected_by
        journey.approval_date = timezone.now()
        journey.approval_comments = reason
        journey.save()

        cls._record_status_change(journey, old_status, 'REJECTED', rejected_by, reason)

        return journey

    @classmethod
    @transaction.atomic
    def start_journey(cls, journey_id: int, user: User) -> JourneyPlan:
        """Start a journey."""
        journey = JourneyPlan.objects.get(id=journey_id, traveler=user)

        if journey.status not in ['APPROVED', 'SUBMITTED']:
            raise ValueError("Journey must be approved before starting")

        old_status = journey.status
        journey.status = 'IN_PROGRESS'
        journey.actual_departure_time = timezone.now()
        journey.save()

        cls._record_status_change(journey, old_status, 'IN_PROGRESS', user)

        return journey

    @classmethod
    @transaction.atomic
    def complete_journey(cls, journey_id: int, user: User, completion_notes: str = '',
                         incidents_reported: bool = False, incident_details: str = '',
                         actual_cost: float = None) -> JourneyPlan:
        """Complete a journey."""
        journey = JourneyPlan.objects.get(id=journey_id, traveler=user)

        if journey.status != 'IN_PROGRESS':
            raise ValueError("Only in-progress journeys can be completed")

        old_status = journey.status
        journey.status = 'COMPLETED'
        journey.actual_return_time = timezone.now()
        journey.completion_notes = completion_notes
        journey.incidents_reported = incidents_reported
        journey.incident_details = incident_details

        if actual_cost is not None:
            journey.actual_cost = actual_cost

        journey.save()

        cls._record_status_change(journey, old_status, 'COMPLETED', user, completion_notes)

        return journey

    @classmethod
    @transaction.atomic
    def cancel_journey(cls, journey_id: int, user: User, reason: str) -> JourneyPlan:
        """Cancel a journey."""
        journey = JourneyPlan.objects.get(id=journey_id)

        if journey.status in ['COMPLETED', 'CANCELLED']:
            raise ValueError("Cannot cancel completed or already cancelled journeys")

        old_status = journey.status
        journey.status = 'CANCELLED'
        journey.save()

        cls._record_status_change(journey, old_status, 'CANCELLED', user, reason)

        return journey

    @classmethod
    def add_waypoint(cls, journey_id: int, waypoint_data: Dict[str, Any]) -> JourneyWaypoint:
        """Add a waypoint to a journey."""
        journey = JourneyPlan.objects.get(id=journey_id)

        # Get next sequence number
        last_waypoint = journey.waypoints.order_by('-sequence').first()
        sequence = last_waypoint.sequence + 1 if last_waypoint else 1

        waypoint = JourneyWaypoint.objects.create(
            journey=journey,
            sequence=sequence,
            location_name=waypoint_data['location_name'],
            address=waypoint_data.get('address', ''),
            gps_coordinates=waypoint_data.get('gps_coordinates', ''),
            planned_arrival_time=waypoint_data.get('planned_arrival_time'),
            planned_departure_time=waypoint_data.get('planned_departure_time'),
            purpose=waypoint_data.get('purpose', ''),
            contact_person=waypoint_data.get('contact_person', ''),
            contact_phone=waypoint_data.get('contact_phone', ''),
            notes=waypoint_data.get('notes', '')
        )

        return waypoint

    @classmethod
    @transaction.atomic
    def check_in(cls, journey_id: int, check_type: str, location_name: str,
                 data: Dict[str, Any]) -> JourneyCheckIn:
        """Record a check-in."""
        journey = JourneyPlan.objects.get(id=journey_id)

        check_in = JourneyCheckIn.objects.create(
            journey=journey,
            waypoint_id=data.get('waypoint_id'),
            check_type=check_type,
            location_name=location_name,
            gps_coordinates=data.get('gps_coordinates', ''),
            notes=data.get('notes', ''),
            vehicle_odometer=data.get('vehicle_odometer'),
            fuel_level=data.get('fuel_level'),
            all_safe=data.get('all_safe', True),
            issues_reported=data.get('issues_reported', ''),
            photo=data.get('photo')
        )

        # Update waypoint if applicable
        if check_in.waypoint:
            if check_type == 'ARRIVAL':
                check_in.waypoint.actual_arrival_time = check_in.check_time
            elif check_type == 'DEPARTURE':
                check_in.waypoint.actual_departure_time = check_in.check_time
                check_in.waypoint.completed = True
            check_in.waypoint.save()

        return check_in

    @classmethod
    def add_document(cls, journey_id: int, document_type: str, title: str,
                     file_obj, uploaded_by: User, notes: str = '') -> JourneyDocument:
        """Add a document to a journey."""
        journey = JourneyPlan.objects.get(id=journey_id)

        document = JourneyDocument.objects.create(
            journey=journey,
            document_type=document_type,
            title=title,
            file=file_obj,
            uploaded_by=uploaded_by,
            notes=notes
        )

        return document

    @classmethod
    def get_active_journeys(cls, user: User = None) -> List[JourneyPlan]:
        """Get active (in-progress) journeys."""
        query = JourneyPlan.objects.filter(status='IN_PROGRESS')

        if user:
            query = query.filter(Q(traveler=user) | Q(companions=user)).distinct()

        return list(query.select_related('traveler', 'approved_by'))

    @classmethod
    def get_overdue_journeys(cls) -> List[JourneyPlan]:
        """Get journeys that are overdue for return."""
        now = timezone.now()

        return list(JourneyPlan.objects.filter(
            status='IN_PROGRESS',
            planned_return_time__lt=now
        ).select_related('traveler'))

    @classmethod
    def get_pending_approvals(cls, approver: User = None) -> List[JourneyPlan]:
        """Get journeys pending approval."""
        query = JourneyPlan.objects.filter(status='SUBMITTED')

        # TODO: Filter by approver permissions/role if needed

        return list(query.select_related('traveler').order_by('submitted_date'))

    @classmethod
    def get_upcoming_journeys(cls, days: int = 7, user: User = None) -> List[JourneyPlan]:
        """Get journeys scheduled in the next X days."""
        start_date = timezone.now()
        end_date = start_date + timedelta(days=days)

        query = JourneyPlan.objects.filter(
            status__in=['APPROVED', 'SUBMITTED'],
            planned_departure_time__gte=start_date,
            planned_departure_time__lte=end_date
        )

        if user:
            query = query.filter(Q(traveler=user) | Q(companions=user)).distinct()

        return list(query.select_related('traveler').order_by('planned_departure_time'))

    @classmethod
    def get_statistics(cls, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get journey statistics."""
        query = JourneyPlan.objects.all()

        if start_date:
            query = query.filter(planned_departure_time__date__gte=start_date)
        if end_date:
            query = query.filter(planned_departure_time__date__lte=end_date)

        return {
            'total': query.count(),
            'by_status': dict(query.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_risk_level': dict(query.values('risk_level').annotate(count=Count('id')).values_list('risk_level', 'count')),
            'active': query.filter(status='IN_PROGRESS').count(),
            'overdue': JourneyPlan.objects.filter(
                status='IN_PROGRESS',
                planned_return_time__lt=timezone.now()
            ).count(),
            'completed': query.filter(status='COMPLETED').count(),
            'with_incidents': query.filter(incidents_reported=True).count(),
        }

    @classmethod
    def _record_status_change(cls, journey: JourneyPlan, from_status: str,
                              to_status: str, changed_by: User, reason: str = ''):
        """Record status change in history."""
        JourneyStatusHistory.objects.create(
            journey=journey,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            reason=reason
        )

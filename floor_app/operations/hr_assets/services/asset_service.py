"""Asset Service - Business logic for HR asset management"""

from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count
from django.db import transaction
from floor_app.operations.hr_assets.models import (
    Vehicle, VehicleAssignment,
    ParkingZone, ParkingSpot, ParkingAssignment,
    SIMCard, SIMAssignment,
    Phone, PhoneAssignment,
    Camera, CameraAssignment
)

User = get_user_model()


class AssetService:
    """Unified service for managing HR assets."""

    # ============================================================================
    # Vehicle Management
    # ============================================================================

    @classmethod
    @transaction.atomic
    def assign_vehicle(cls, vehicle_id: int, assigned_to: User, assigned_by: User,
                       start_date: date, end_date: date = None, purpose: str = '',
                       start_odometer: int = None) -> VehicleAssignment:
        """Assign a vehicle to an employee."""
        vehicle = Vehicle.objects.get(id=vehicle_id)

        if vehicle.status not in ['AVAILABLE', 'ASSIGNED']:
            raise ValueError(f"Vehicle is not available (status: {vehicle.status})")

        # End previous active assignments
        VehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Create new assignment
        assignment = VehicleAssignment.objects.create(
            vehicle=vehicle,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            start_odometer=start_odometer or vehicle.current_odometer,
            is_active=True
        )

        # Update vehicle
        vehicle.status = 'ASSIGNED'
        vehicle.assigned_to = assigned_to
        vehicle.assignment_date = start_date
        vehicle.save()

        return assignment

    @classmethod
    @transaction.atomic
    def return_vehicle(cls, vehicle_id: int, end_odometer: int = None, notes: str = ''):
        """Return a vehicle."""
        vehicle = Vehicle.objects.get(id=vehicle_id)

        # Update active assignment
        assignment = VehicleAssignment.objects.filter(
            vehicle=vehicle, is_active=True
        ).first()

        if assignment:
            assignment.end_date = timezone.now().date()
            assignment.end_odometer = end_odometer or vehicle.current_odometer
            assignment.notes = notes
            assignment.is_active = False
            assignment.save()

        # Update vehicle
        vehicle.status = 'AVAILABLE'
        vehicle.assigned_to = None
        vehicle.assignment_date = None
        if end_odometer:
            vehicle.current_odometer = end_odometer
        vehicle.save()

        return vehicle

    @classmethod
    def get_available_vehicles(cls) -> List[Vehicle]:
        """Get all available vehicles."""
        return list(Vehicle.objects.filter(status='AVAILABLE'))

    @classmethod
    def get_vehicles_due_for_service(cls, days_ahead: int = 30) -> List[Vehicle]:
        """Get vehicles due for service."""
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)

        return list(Vehicle.objects.filter(
            Q(next_service_due__lte=future_date) | Q(next_service_due__isnull=True),
            status__in=['AVAILABLE', 'ASSIGNED', 'IN_USE']
        ))

    # ============================================================================
    # Parking Management
    # ============================================================================

    @classmethod
    @transaction.atomic
    def assign_parking(cls, spot_id: int, assigned_to: User, assigned_by: User,
                       start_date: date, end_date: date = None,
                       vehicle: Vehicle = None) -> ParkingAssignment:
        """Assign a parking spot to an employee."""
        spot = ParkingSpot.objects.get(id=spot_id)

        if spot.status not in ['AVAILABLE']:
            raise ValueError(f"Parking spot is not available (status: {spot.status})")

        # End previous active assignments
        ParkingAssignment.objects.filter(
            spot=spot, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Create new assignment
        assignment = ParkingAssignment.objects.create(
            spot=spot,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            start_date=start_date,
            end_date=end_date,
            vehicle=vehicle,
            is_active=True
        )

        # Update spot
        spot.status = 'ASSIGNED'
        spot.assigned_to = assigned_to
        spot.assignment_date = start_date
        spot.assignment_end_date = end_date
        spot.save()

        return assignment

    @classmethod
    @transaction.atomic
    def release_parking(cls, spot_id: int):
        """Release a parking spot."""
        spot = ParkingSpot.objects.get(id=spot_id)

        # Update active assignment
        ParkingAssignment.objects.filter(
            spot=spot, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Update spot
        spot.status = 'AVAILABLE'
        spot.assigned_to = None
        spot.assignment_date = None
        spot.assignment_end_date = None
        spot.save()

        return spot

    @classmethod
    def get_available_parking(cls, zone_id: int = None, spot_type: str = None) -> List[ParkingSpot]:
        """Get available parking spots."""
        query = ParkingSpot.objects.filter(status='AVAILABLE', is_active=True)

        if zone_id:
            query = query.filter(zone_id=zone_id)
        if spot_type:
            query = query.filter(spot_type=spot_type)

        return list(query.select_related('zone'))

    # ============================================================================
    # SIM Card Management
    # ============================================================================

    @classmethod
    @transaction.atomic
    def assign_sim(cls, sim_id: int, assigned_to: User, assigned_by: User,
                   start_date: date, end_date: date = None, purpose: str = '') -> SIMAssignment:
        """Assign a SIM card to an employee."""
        sim = SIMCard.objects.get(id=sim_id)

        if sim.status not in ['AVAILABLE']:
            raise ValueError(f"SIM card is not available (status: {sim.status})")

        # End previous active assignments
        SIMAssignment.objects.filter(
            sim=sim, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Create new assignment
        assignment = SIMAssignment.objects.create(
            sim=sim,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            is_active=True
        )

        # Update SIM
        sim.status = 'ASSIGNED'
        sim.assigned_to = assigned_to
        sim.assignment_date = start_date
        sim.save()

        return assignment

    @classmethod
    @transaction.atomic
    def return_sim(cls, sim_id: int, notes: str = ''):
        """Return a SIM card."""
        sim = SIMCard.objects.get(id=sim_id)

        # Update active assignment
        SIMAssignment.objects.filter(
            sim=sim, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Update SIM
        sim.status = 'AVAILABLE'
        sim.assigned_to = None
        sim.assignment_date = None
        sim.save()

        return sim

    @classmethod
    def get_sims_expiring_soon(cls, days_ahead: int = 30) -> List[SIMCard]:
        """Get SIM cards expiring soon."""
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)

        return list(SIMCard.objects.filter(
            expiry_date__lte=future_date,
            status__in=['ASSIGNED', 'ACTIVE']
        ))

    # ============================================================================
    # Phone Management
    # ============================================================================

    @classmethod
    @transaction.atomic
    def assign_phone(cls, phone_id: int, assigned_to: User, assigned_by: User,
                     start_date: date, end_date: date = None, purpose: str = '',
                     condition: str = 'GOOD') -> PhoneAssignment:
        """Assign a phone to an employee."""
        phone = Phone.objects.get(id=phone_id)

        if phone.status not in ['AVAILABLE']:
            raise ValueError(f"Phone is not available (status: {phone.status})")

        # End previous active assignments
        PhoneAssignment.objects.filter(
            phone=phone, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Create new assignment
        assignment = PhoneAssignment.objects.create(
            phone=phone,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            condition_at_assignment=condition,
            is_active=True
        )

        # Update phone
        phone.status = 'ASSIGNED'
        phone.assigned_to = assigned_to
        phone.assignment_date = start_date
        phone.save()

        return assignment

    @classmethod
    @transaction.atomic
    def return_phone(cls, phone_id: int, condition: str = 'GOOD', notes: str = ''):
        """Return a phone."""
        phone = Phone.objects.get(id=phone_id)

        # Update active assignment
        assignment = PhoneAssignment.objects.filter(
            phone=phone, is_active=True
        ).first()

        if assignment:
            assignment.end_date = timezone.now().date()
            assignment.condition_at_return = condition
            assignment.notes = notes
            assignment.is_active = False
            assignment.save()

        # Update phone
        phone.status = 'AVAILABLE'
        phone.assigned_to = None
        phone.assignment_date = None
        phone.save()

        return phone

    @classmethod
    def get_phones_warranty_expiring(cls, days_ahead: int = 30) -> List[Phone]:
        """Get phones with warranty expiring soon."""
        today = timezone.now().date()
        future_date = today + timedelta(days=days_ahead)

        return list(Phone.objects.filter(
            warranty_expiry__lte=future_date,
            warranty_expiry__gte=today,
            status__in=['AVAILABLE', 'ASSIGNED', 'IN_USE']
        ))

    # ============================================================================
    # Camera Management
    # ============================================================================

    @classmethod
    @transaction.atomic
    def assign_camera(cls, camera_id: int, assigned_to: User, assigned_by: User,
                      start_date: date, end_date: date = None, purpose: str = '',
                      project: str = '', condition: str = 'GOOD',
                      accessories: List[str] = None) -> CameraAssignment:
        """Assign a camera to an employee."""
        camera = Camera.objects.get(id=camera_id)

        if camera.status not in ['AVAILABLE']:
            raise ValueError(f"Camera is not available (status: {camera.status})")

        # End previous active assignments
        CameraAssignment.objects.filter(
            camera=camera, is_active=True
        ).update(is_active=False, end_date=timezone.now().date())

        # Create new assignment
        assignment = CameraAssignment.objects.create(
            camera=camera,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            project=project,
            condition_at_assignment=condition,
            accessories_given=accessories or [],
            is_active=True
        )

        # Update camera
        camera.status = 'ASSIGNED'
        camera.assigned_to = assigned_to
        camera.assignment_date = start_date
        camera.save()

        return assignment

    @classmethod
    @transaction.atomic
    def return_camera(cls, camera_id: int, condition: str = 'GOOD',
                      accessories_returned: List[str] = None, notes: str = ''):
        """Return a camera."""
        camera = Camera.objects.get(id=camera_id)

        # Update active assignment
        assignment = CameraAssignment.objects.filter(
            camera=camera, is_active=True
        ).first()

        if assignment:
            assignment.end_date = timezone.now().date()
            assignment.condition_at_return = condition
            assignment.accessories_returned = accessories_returned or []
            assignment.notes = notes
            assignment.is_active = False
            assignment.save()

        # Update camera
        camera.status = 'AVAILABLE'
        camera.assigned_to = None
        camera.assignment_date = None
        camera.save()

        return camera

    # ============================================================================
    # General Asset Queries
    # ============================================================================

    @classmethod
    def get_user_assets(cls, user: User) -> Dict[str, List]:
        """Get all assets assigned to a user."""
        return {
            'vehicles': list(Vehicle.objects.filter(assigned_to=user)),
            'parking_spots': list(ParkingSpot.objects.filter(assigned_to=user)),
            'sim_cards': list(SIMCard.objects.filter(assigned_to=user)),
            'phones': list(Phone.objects.filter(assigned_to=user)),
            'cameras': list(Camera.objects.filter(assigned_to=user)),
        }

    @classmethod
    def get_asset_statistics(cls) -> Dict[str, Any]:
        """Get overall asset statistics."""
        return {
            'vehicles': {
                'total': Vehicle.objects.count(),
                'available': Vehicle.objects.filter(status='AVAILABLE').count(),
                'assigned': Vehicle.objects.filter(status='ASSIGNED').count(),
                'maintenance': Vehicle.objects.filter(status='MAINTENANCE').count(),
            },
            'parking': {
                'total': ParkingSpot.objects.count(),
                'available': ParkingSpot.objects.filter(status='AVAILABLE').count(),
                'assigned': ParkingSpot.objects.filter(status='ASSIGNED').count(),
            },
            'sim_cards': {
                'total': SIMCard.objects.count(),
                'available': SIMCard.objects.filter(status='AVAILABLE').count(),
                'assigned': SIMCard.objects.filter(status='ASSIGNED').count(),
            },
            'phones': {
                'total': Phone.objects.count(),
                'available': Phone.objects.filter(status='AVAILABLE').count(),
                'assigned': Phone.objects.filter(status='ASSIGNED').count(),
            },
            'cameras': {
                'total': Camera.objects.count(),
                'available': Camera.objects.filter(status='AVAILABLE').count(),
                'assigned': Camera.objects.filter(status='ASSIGNED').count(),
            },
        }

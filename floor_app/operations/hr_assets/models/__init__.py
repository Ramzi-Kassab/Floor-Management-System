"""
HR Asset Management Models

Models for managing company assets: vehicles, parking, SIM cards, phones, cameras, etc.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from floor_app.mixins import AuditMixin


# ============================================================================
# Vehicle Management
# ============================================================================

class Vehicle(AuditMixin):
    """Company vehicles."""

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('IN_USE', 'In Use'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('RETIRED', 'Retired'),
    )

    VEHICLE_TYPES = (
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('BUS', 'Bus'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('FORKLIFT', 'Forklift'),
        ('OTHER', 'Other'),
    )

    vehicle_number = models.CharField(max_length=50, unique=True, help_text="Vehicle ID/number")
    plate_number = models.CharField(max_length=50, unique=True, help_text="License plate number")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, help_text="Type of vehicle")
    make = models.CharField(max_length=50, help_text="Manufacturer")
    model = models.CharField(max_length=50, help_text="Model")
    year = models.IntegerField(help_text="Manufacturing year")
    color = models.CharField(max_length=30, blank=True, help_text="Vehicle color")
    vin_number = models.CharField(max_length=50, blank=True, unique=True, null=True, help_text="VIN number")

    # Capacity
    seating_capacity = models.IntegerField(null=True, blank=True, help_text="Number of seats")
    load_capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Load capacity in kg")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles')
    assignment_date = models.DateField(null=True, blank=True)

    # Details
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_odometer = models.IntegerField(default=0, help_text="Current odometer reading (km)")
    fuel_type = models.CharField(max_length=20, choices=(
        ('PETROL', 'Petrol'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
        ('CNG', 'CNG'),
    ), default='PETROL')
    fuel_card_number = models.CharField(max_length=50, blank=True)

    # Insurance & Registration
    insurance_company = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)
    registration_expiry_date = models.DateField(null=True, blank=True)

    # Maintenance
    last_service_date = models.DateField(null=True, blank=True)
    last_service_odometer = models.IntegerField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)
    service_interval_km = models.IntegerField(default=5000, help_text="Service interval in km")

    # Location
    current_location = models.CharField(max_length=200, blank=True)
    parking_spot = models.ForeignKey('ParkingSpot', on_delete=models.SET_NULL, null=True, blank=True, related_name='parked_vehicles')

    # Additional
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    documents = models.JSONField(default=dict, blank=True, help_text="Document references")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hr_vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['vehicle_number']

    def __str__(self):
        return f"{self.vehicle_number} - {self.make} {self.model}"


class VehicleAssignment(AuditMixin):
    """Vehicle assignment history."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vehicle_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='vehicle_assignments_made')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    start_odometer = models.IntegerField(null=True, blank=True)
    end_odometer = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_vehicle_assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.vehicle.vehicle_number} → {self.assigned_to.get_full_name()}"


# ============================================================================
# Parking Management
# ============================================================================

class ParkingZone(AuditMixin):
    """Parking zones/areas."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Physical location")
    building = models.CharField(max_length=100, blank=True)
    floor_level = models.CharField(max_length=50, blank=True)
    total_spots = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_covered = models.BooleanField(default=False)
    is_secure = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_parking_zones'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ParkingSpot(AuditMixin):
    """Individual parking spots."""

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('OCCUPIED', 'Occupied'),
        ('RESERVED', 'Reserved'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('DISABLED', 'Disabled'),
    )

    SPOT_TYPES = (
        ('STANDARD', 'Standard'),
        ('COMPACT', 'Compact'),
        ('LARGE', 'Large/Truck'),
        ('DISABLED', 'Disabled Access'),
        ('EV_CHARGING', 'EV Charging'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('VISITOR', 'Visitor'),
        ('EXECUTIVE', 'Executive'),
    )

    zone = models.ForeignKey(ParkingZone, on_delete=models.CASCADE, related_name='spots')
    spot_number = models.CharField(max_length=20, help_text="Spot number/identifier")
    spot_type = models.CharField(max_length=20, choices=SPOT_TYPES, default='STANDARD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_parking_spots')
    assignment_date = models.DateField(null=True, blank=True)
    assignment_end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_parking_spots'
        unique_together = [['zone', 'spot_number']]
        ordering = ['zone', 'spot_number']

    def __str__(self):
        return f"{self.zone.code}-{self.spot_number}"


class ParkingAssignment(AuditMixin):
    """Parking spot assignment history."""

    spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='parking_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='parking_assignments_made')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='parking_assignments')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_parking_assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.spot} → {self.assigned_to.get_full_name()}"


# ============================================================================
# SIM Card Management
# ============================================================================

class SIMCard(AuditMixin):
    """Company SIM cards."""

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
        ('TERMINATED', 'Terminated'),
    )

    sim_number = models.CharField(max_length=50, unique=True, help_text="SIM card number/ICCID")
    phone_number = models.CharField(max_length=20, unique=True, help_text="Phone number")
    carrier = models.CharField(max_length=50, help_text="Mobile carrier/provider")
    plan_type = models.CharField(max_length=50, blank=True, help_text="Data plan type")
    monthly_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    data_limit_gb = models.IntegerField(null=True, blank=True, help_text="Monthly data limit (GB)")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_sims')
    assignment_date = models.DateField(null=True, blank=True)

    # Dates
    activation_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    last_recharge_date = models.DateField(null=True, blank=True)

    # Details
    pin_code = models.CharField(max_length=20, blank=True, help_text="PIN code (encrypted)")
    puk_code = models.CharField(max_length=20, blank=True, help_text="PUK code (encrypted)")
    account_number = models.CharField(max_length=50, blank=True, help_text="Carrier account number")

    # Usage
    current_usage_gb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_usage_update = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hr_sim_cards'
        ordering = ['phone_number']

    def __str__(self):
        return f"{self.phone_number} ({self.carrier})"


class SIMAssignment(AuditMixin):
    """SIM card assignment history."""

    sim = models.ForeignKey(SIMCard, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sim_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sim_assignments_made')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_sim_assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.sim.phone_number} → {self.assigned_to.get_full_name()}"


# ============================================================================
# Phone Management
# ============================================================================

class Phone(AuditMixin):
    """Company phones/mobile devices."""

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('IN_USE', 'In Use'),
        ('REPAIR', 'Under Repair'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
        ('RETIRED', 'Retired'),
    )

    device_id = models.CharField(max_length=50, unique=True, help_text="Device ID/Serial number")
    imei = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="IMEI number")
    make = models.CharField(max_length=50, help_text="Manufacturer")
    model = models.CharField(max_length=50, help_text="Model")
    os = models.CharField(max_length=20, choices=(
        ('IOS', 'iOS'),
        ('ANDROID', 'Android'),
        ('OTHER', 'Other'),
    ), help_text="Operating system")
    os_version = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_phones')
    assignment_date = models.DateField(null=True, blank=True)

    # Details
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)

    # SIM
    sim_card = models.ForeignKey(SIMCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='phones')

    # Accessories
    has_charger = models.BooleanField(default=True)
    has_case = models.BooleanField(default=False)
    has_screen_protector = models.BooleanField(default=False)
    accessories_notes = models.TextField(blank=True)

    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='phones/', null=True, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hr_phones'
        ordering = ['device_id']

    def __str__(self):
        return f"{self.device_id} - {self.make} {self.model}"


class PhoneAssignment(AuditMixin):
    """Phone assignment history."""

    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='phone_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='phone_assignments_made')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    condition_at_assignment = models.CharField(max_length=20, choices=(
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
    ), default='GOOD')
    condition_at_return = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_phone_assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.phone.device_id} → {self.assigned_to.get_full_name()}"


# ============================================================================
# Camera Management
# ============================================================================

class Camera(AuditMixin):
    """Company cameras and equipment."""

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('IN_USE', 'In Use'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('REPAIR', 'Under Repair'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
        ('RETIRED', 'Retired'),
    )

    CAMERA_TYPES = (
        ('DSLR', 'DSLR'),
        ('MIRRORLESS', 'Mirrorless'),
        ('POINT_SHOOT', 'Point & Shoot'),
        ('ACTION', 'Action Camera'),
        ('VIDEO', 'Video Camera'),
        ('SECURITY', 'Security Camera'),
        ('DRONE', 'Drone with Camera'),
        ('OTHER', 'Other'),
    )

    camera_id = models.CharField(max_length=50, unique=True, help_text="Camera ID/Asset tag")
    serial_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    camera_type = models.CharField(max_length=20, choices=CAMERA_TYPES, default='DSLR')
    make = models.CharField(max_length=50, help_text="Manufacturer")
    model = models.CharField(max_length=50, help_text="Model")

    # Specifications
    megapixels = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sensor_size = models.CharField(max_length=50, blank=True)
    video_resolution = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cameras')
    assignment_date = models.DateField(null=True, blank=True)

    # Details
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Accessories & Equipment
    lenses = models.JSONField(default=list, blank=True, help_text="List of lenses")
    accessories = models.JSONField(default=list, blank=True, help_text="Other accessories")
    memory_cards = models.JSONField(default=list, blank=True)
    batteries = models.IntegerField(default=1, help_text="Number of batteries")
    has_bag = models.BooleanField(default=False)
    has_tripod = models.BooleanField(default=False)

    # Maintenance
    last_service_date = models.DateField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='cameras/', null=True, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'hr_cameras'
        ordering = ['camera_id']

    def __str__(self):
        return f"{self.camera_id} - {self.make} {self.model}"


class CameraAssignment(AuditMixin):
    """Camera assignment history."""

    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='camera_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='camera_assignments_made')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    project = models.CharField(max_length=100, blank=True, help_text="Project name")
    condition_at_assignment = models.CharField(max_length=20, choices=(
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
    ), default='GOOD')
    condition_at_return = models.CharField(max_length=20, blank=True)
    accessories_given = models.JSONField(default=list, blank=True)
    accessories_returned = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_camera_assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.camera.camera_id} → {self.assigned_to.get_full_name()}"

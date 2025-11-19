"""
GPS Verification Service

Calculate distances, verify locations, reverse geocode, etc.
"""

import math
from typing import Tuple, Optional
from decimal import Decimal


class GPSVerificationService:
    """
    Service for GPS-related calculations and verifications.

    Uses Haversine formula for distance calculations.
    """

    EARTH_RADIUS_METERS = 6371000  # Earth's radius in meters

    @classmethod
    def calculate_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.

        Args:
            lat1: Latitude of point 1 (degrees)
            lon1: Longitude of point 1 (degrees)
            lat2: Latitude of point 2 (degrees)
            lon2: Longitude of point 2 (degrees)

        Returns:
            Distance in meters

        Example:
            distance = GPSVerificationService.calculate_distance(
                24.1234, 55.5678,  # Point 1 (Dubai)
                24.1250, 55.5690   # Point 2
            )
            # Returns: ~180 meters
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        distance = cls.EARTH_RADIUS_METERS * c

        return distance

    @classmethod
    def is_within_radius(
        cls,
        center_lat: float,
        center_lon: float,
        point_lat: float,
        point_lon: float,
        radius_meters: float
    ) -> Tuple[bool, float]:
        """
        Check if a point is within a circular geofence.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            point_lat: Point latitude to check
            point_lon: Point longitude to check
            radius_meters: Geofence radius in meters

        Returns:
            Tuple of (is_within, distance_meters)

        Example:
            is_within, distance = GPSVerificationService.is_within_radius(
                24.1234, 55.5678,  # Warehouse center
                24.1240, 55.5680,  # Employee location
                100                # 100m radius
            )
        """
        distance = cls.calculate_distance(center_lat, center_lon, point_lat, point_lon)
        is_within = distance <= radius_meters

        return is_within, distance

    @classmethod
    def is_point_in_polygon(
        cls,
        latitude: float,
        longitude: float,
        polygon_points: list
    ) -> bool:
        """
        Check if a point is inside a polygon (ray casting algorithm).

        Args:
            latitude: Point latitude
            longitude: Point longitude
            polygon_points: List of dicts with 'lat' and 'lon' keys

        Returns:
            True if inside polygon, False otherwise

        Example:
            polygon = [
                {'lat': 24.1234, 'lon': 55.5678},
                {'lat': 24.1240, 'lon': 55.5680},
                {'lat': 24.1238, 'lon': 55.5690},
                {'lat': 24.1232, 'lon': 55.5688},
            ]
            is_inside = GPSVerificationService.is_point_in_polygon(
                24.1236, 55.5684,
                polygon
            )
        """
        if not polygon_points or len(polygon_points) < 3:
            return False

        # Ray casting algorithm
        n = len(polygon_points)
        inside = False

        p1_lat, p1_lon = polygon_points[0]['lat'], polygon_points[0]['lon']

        for i in range(1, n + 1):
            p2_lat, p2_lon = polygon_points[i % n]['lat'], polygon_points[i % n]['lon']

            if longitude > min(p1_lon, p2_lon):
                if longitude <= max(p1_lon, p2_lon):
                    if latitude <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            x_intersection = (
                                (longitude - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon)
                                + p1_lat
                            )
                            if p1_lat == p2_lat or latitude <= x_intersection:
                                inside = not inside

            p1_lat, p1_lon = p2_lat, p2_lon

        return inside

    @classmethod
    def reverse_geocode(
        cls,
        latitude: float,
        longitude: float,
        use_service: str = 'nominatim'
    ) -> str:
        """
        Reverse geocode GPS coordinates to human-readable address.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            use_service: Geocoding service ('nominatim', 'google', etc.)

        Returns:
            Address string

        Note:
            Requires geopy library and internet connection.
            May have rate limits.

        Example:
            address = GPSVerificationService.reverse_geocode(
                24.1234, 55.5678
            )
            # Returns: "Sheikh Zayed Road, Dubai, UAE"
        """
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeopyError

            # Create geocoder (with user agent to respect ToS)
            geolocator = Nominatim(user_agent="floor_management_system")

            # Reverse geocode
            location = geolocator.reverse(f"{latitude}, {longitude}", timeout=5)

            if location:
                return location.address

            return f"{latitude}, {longitude}"

        except ImportError:
            # geopy not installed
            return f"{latitude}, {longitude}"
        except Exception as e:
            # Geocoding failed
            return f"{latitude}, {longitude}"

    @classmethod
    def forward_geocode(cls, address: str) -> Optional[Tuple[float, float]]:
        """
        Forward geocode address to GPS coordinates.

        Args:
            address: Address string

        Returns:
            Tuple of (latitude, longitude) or None

        Example:
            coords = GPSVerificationService.forward_geocode(
                "Sheikh Zayed Road, Dubai, UAE"
            )
            # Returns: (24.1234, 55.5678)
        """
        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="floor_management_system")
            location = geolocator.geocode(address, timeout=5)

            if location:
                return (location.latitude, location.longitude)

            return None

        except ImportError:
            return None
        except Exception as e:
            return None

    @classmethod
    def verify_location(
        cls,
        expected_lat: float,
        expected_lon: float,
        actual_lat: float,
        actual_lon: float,
        radius_meters: int = 100
    ) -> dict:
        """
        Complete location verification with all details.

        Args:
            expected_lat: Expected latitude
            expected_lon: Expected longitude
            actual_lat: Actual latitude
            actual_lon: Actual longitude
            radius_meters: Geofence radius

        Returns:
            Dict with verification results

        Example:
            result = GPSVerificationService.verify_location(
                24.1234, 55.5678,  # Expected
                24.1240, 55.5680,  # Actual
                100                # 100m radius
            )
            # Returns:
            # {
            #     'is_verified': True,
            #     'distance_meters': 78.5,
            #     'is_within_geofence': True,
            #     'accuracy': 'HIGH',
            #     'message': 'Location verified within 100m geofence'
            # }
        """
        # Calculate distance
        distance = cls.calculate_distance(
            expected_lat, expected_lon,
            actual_lat, actual_lon
        )

        # Check if within geofence
        is_within = distance <= radius_meters

        # Determine accuracy level
        if distance <= radius_meters * 0.25:
            accuracy = 'VERY_HIGH'
        elif distance <= radius_meters * 0.5:
            accuracy = 'HIGH'
        elif distance <= radius_meters:
            accuracy = 'MEDIUM'
        elif distance <= radius_meters * 2:
            accuracy = 'LOW'
        else:
            accuracy = 'VERY_LOW'

        # Create message
        if is_within:
            message = f"Location verified within {radius_meters}m geofence ({distance:.1f}m away)"
        else:
            message = f"Location NOT verified: {distance:.1f}m away (geofence: {radius_meters}m)"

        return {
            'is_verified': is_within,
            'distance_meters': round(distance, 2),
            'is_within_geofence': is_within,
            'accuracy': accuracy,
            'message': message,
            'expected_coords': (expected_lat, expected_lon),
            'actual_coords': (actual_lat, actual_lon),
        }

    @classmethod
    def get_current_position_accuracy(cls, gps_accuracy: float) -> str:
        """
        Determine GPS accuracy level.

        Args:
            gps_accuracy: GPS accuracy in meters (from device)

        Returns:
            Accuracy level string

        GPS Accuracy Levels:
        - < 5m: Excellent (indoor/pinpoint)
        - 5-10m: Very Good (outdoor)
        - 10-20m: Good (normal GPS)
        - 20-50m: Fair (weak signal)
        - > 50m: Poor (bad conditions)
        """
        if gps_accuracy < 5:
            return 'EXCELLENT'
        elif gps_accuracy < 10:
            return 'VERY_GOOD'
        elif gps_accuracy < 20:
            return 'GOOD'
        elif gps_accuracy < 50:
            return 'FAIR'
        else:
            return 'POOR'

    @classmethod
    def calculate_bearing(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate bearing (direction) from point 1 to point 2.

        Args:
            lat1, lon1: Starting point
            lat2, lon2: Destination point

        Returns:
            Bearing in degrees (0-360)
            0° = North, 90° = East, 180° = South, 270° = West

        Example:
            bearing = GPSVerificationService.calculate_bearing(
                24.1234, 55.5678,  # From
                24.1250, 55.5690   # To
            )
            # Returns: ~45° (Northeast)
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (
            math.cos(lat1_rad) * math.sin(lat2_rad) -
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        )

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        # Normalize to 0-360
        bearing_deg = (bearing_deg + 360) % 360

        return bearing_deg

    @classmethod
    def get_direction_name(cls, bearing: float) -> str:
        """
        Convert bearing to compass direction name.

        Args:
            bearing: Bearing in degrees (0-360)

        Returns:
            Direction name (N, NE, E, SE, S, SW, W, NW)

        Example:
            direction = GPSVerificationService.get_direction_name(45)
            # Returns: "NE" (Northeast)
        """
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = round(bearing / 45) % 8
        return directions[index]

"""
Calculator and Converter Tools Service

Date calculators, unit converters, color converters, etc.
"""

from datetime import datetime, timedelta
from typing import Tuple
import re


class CalculatorToolsService:
    """
    Service for calculator and converter operations.
    """

    # ==================== Date/Time Calculators ====================

    @classmethod
    def date_diff(cls, date1: str, date2: str, unit: str = 'days') -> int:
        """
        Calculate difference between two dates.

        Args:
            date1: First date (YYYY-MM-DD)
            date2: Second date (YYYY-MM-DD)
            unit: Result unit (days, weeks, months, years)

        Returns:
            Difference in specified unit

        Example:
            diff = CalculatorToolsService.date_diff("2024-01-01", "2024-12-31", "days")
        """
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        diff = abs((d2 - d1).days)

        if unit == 'days':
            return diff
        elif unit == 'weeks':
            return diff // 7
        elif unit == 'months':
            return diff // 30  # Approximate
        elif unit == 'years':
            return diff // 365  # Approximate
        else:
            raise ValueError(f"Unknown unit: {unit}")

    @classmethod
    def add_days(cls, date: str, days: int) -> str:
        """
        Add days to a date.

        Args:
            date: Date (YYYY-MM-DD)
            days: Number of days to add (can be negative)

        Returns:
            New date (YYYY-MM-DD)

        Example:
            new_date = CalculatorToolsService.add_days("2024-01-01", 30)
        """
        d = datetime.strptime(date, '%Y-%m-%d')
        new_date = d + timedelta(days=days)
        return new_date.strftime('%Y-%m-%d')

    @classmethod
    def business_days_between(cls, date1: str, date2: str, holidays: list = None) -> int:
        """
        Calculate business days between two dates.

        Args:
            date1: Start date (YYYY-MM-DD)
            date2: End date (YYYY-MM-DD)
            holidays: List of holiday dates (YYYY-MM-DD)

        Returns:
            Number of business days

        Example:
            days = CalculatorToolsService.business_days_between(
                "2024-01-01", "2024-01-31",
                holidays=["2024-01-15"]
            )
        """
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')

        if d1 > d2:
            d1, d2 = d2, d1

        holidays_set = set(holidays or [])
        business_days = 0

        current = d1
        while current <= d2:
            # Check if not weekend (Monday=0, Sunday=6)
            if current.weekday() < 5:  # Monday to Friday
                # Check if not a holiday
                if current.strftime('%Y-%m-%d') not in holidays_set:
                    business_days += 1

            current += timedelta(days=1)

        return business_days

    @classmethod
    def age_calculator(cls, birth_date: str, reference_date: str = None) -> dict:
        """
        Calculate age from birth date.

        Args:
            birth_date: Birth date (YYYY-MM-DD)
            reference_date: Reference date (default: today)

        Returns:
            Dict with years, months, days

        Example:
            age = CalculatorToolsService.age_calculator("1990-05-15")
            # Returns: {'years': 34, 'months': 8, 'days': 3, ...}
        """
        birth = datetime.strptime(birth_date, '%Y-%m-%d')

        if reference_date:
            ref = datetime.strptime(reference_date, '%Y-%m-%d')
        else:
            ref = datetime.now()

        years = ref.year - birth.year
        months = ref.month - birth.month
        days = ref.day - birth.day

        # Adjust for negative days
        if days < 0:
            months -= 1
            # Get days in previous month
            prev_month = ref.month - 1 if ref.month > 1 else 12
            prev_year = ref.year if ref.month > 1 else ref.year - 1
            days_in_prev_month = (datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)).day if prev_month < 12 else 31
            days += days_in_prev_month

        # Adjust for negative months
        if months < 0:
            years -= 1
            months += 12

        total_days = (ref - birth).days

        return {
            'years': years,
            'months': months,
            'days': days,
            'total_days': total_days,
            'total_weeks': total_days // 7,
            'total_months': years * 12 + months,
        }

    # ==================== Unit Converters ====================

    @classmethod
    def convert_length(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between length units.

        Args:
            value: Value to convert
            from_unit: Source unit (mm, cm, m, km, in, ft, yd, mi)
            to_unit: Target unit

        Returns:
            Converted value

        Example:
            meters = CalculatorToolsService.convert_length(100, 'cm', 'm')
        """
        # Convert to meters first
        to_meters = {
            'mm': 0.001,
            'cm': 0.01,
            'm': 1.0,
            'km': 1000.0,
            'in': 0.0254,
            'ft': 0.3048,
            'yd': 0.9144,
            'mi': 1609.34,
        }

        if from_unit not in to_meters or to_unit not in to_meters:
            raise ValueError(f"Unknown unit: {from_unit} or {to_unit}")

        # Convert to meters, then to target unit
        meters = value * to_meters[from_unit]
        result = meters / to_meters[to_unit]

        return round(result, 6)

    @classmethod
    def convert_weight(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between weight units.

        Args:
            value: Value to convert
            from_unit: Source unit (mg, g, kg, ton, oz, lb)
            to_unit: Target unit

        Returns:
            Converted value

        Example:
            kg = CalculatorToolsService.convert_weight(1000, 'g', 'kg')
        """
        # Convert to grams first
        to_grams = {
            'mg': 0.001,
            'g': 1.0,
            'kg': 1000.0,
            'ton': 1000000.0,
            'oz': 28.3495,
            'lb': 453.592,
        }

        if from_unit not in to_grams or to_unit not in to_grams:
            raise ValueError(f"Unknown unit: {from_unit} or {to_unit}")

        grams = value * to_grams[from_unit]
        result = grams / to_grams[to_unit]

        return round(result, 6)

    @classmethod
    def convert_temperature(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between temperature units.

        Args:
            value: Value to convert
            from_unit: Source unit (C, F, K)
            to_unit: Target unit

        Returns:
            Converted value

        Example:
            fahrenheit = CalculatorToolsService.convert_temperature(100, 'C', 'F')
        """
        # Convert to Celsius first
        if from_unit == 'C':
            celsius = value
        elif from_unit == 'F':
            celsius = (value - 32) * 5/9
        elif from_unit == 'K':
            celsius = value - 273.15
        else:
            raise ValueError(f"Unknown unit: {from_unit}")

        # Convert from Celsius to target
        if to_unit == 'C':
            result = celsius
        elif to_unit == 'F':
            result = celsius * 9/5 + 32
        elif to_unit == 'K':
            result = celsius + 273.15
        else:
            raise ValueError(f"Unknown unit: {to_unit}")

        return round(result, 2)

    # ==================== Color Converters ====================

    @classmethod
    def hex_to_rgb(cls, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB.

        Args:
            hex_color: Hex color code (#RRGGBB or RRGGBB)

        Returns:
            Tuple of (R, G, B)

        Example:
            rgb = CalculatorToolsService.hex_to_rgb("#FF5733")
        """
        hex_color = hex_color.lstrip('#')

        if len(hex_color) != 6:
            raise ValueError("Invalid hex color format")

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return (r, g, b)

    @classmethod
    def rgb_to_hex(cls, r: int, g: int, b: int) -> str:
        """
        Convert RGB to hex color.

        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)

        Returns:
            Hex color code (#RRGGBB)

        Example:
            hex_color = CalculatorToolsService.rgb_to_hex(255, 87, 51)
        """
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("RGB values must be between 0 and 255")

        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def rgb_to_hsl(cls, r: int, g: int, b: int) -> Tuple[int, int, int]:
        """
        Convert RGB to HSL.

        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)

        Returns:
            Tuple of (H, S, L) where H is 0-360, S and L are 0-100

        Example:
            hsl = CalculatorToolsService.rgb_to_hsl(255, 87, 51)
        """
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2.0

        if max_c == min_c:
            h = s = 0.0
        else:
            d = max_c - min_c
            s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)

            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4

            h /= 6.0

        h = int(h * 360)
        s = int(s * 100)
        l = int(l * 100)

        return (h, s, l)

    # ==================== Number Base Converters ====================

    @classmethod
    def convert_base(cls, number: str, from_base: int, to_base: int) -> str:
        """
        Convert number between bases.

        Args:
            number: Number as string
            from_base: Source base (2-36)
            to_base: Target base (2-36)

        Returns:
            Converted number as string

        Example:
            binary = CalculatorToolsService.convert_base("255", 10, 2)
            # Returns: "11111111"
        """
        if not (2 <= from_base <= 36 and 2 <= to_base <= 36):
            raise ValueError("Bases must be between 2 and 36")

        # Convert to decimal first
        decimal = int(number, from_base)

        # Convert to target base
        if to_base == 10:
            return str(decimal)

        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = ""

        while decimal > 0:
            result = digits[decimal % to_base] + result
            decimal //= to_base

        return result or "0"

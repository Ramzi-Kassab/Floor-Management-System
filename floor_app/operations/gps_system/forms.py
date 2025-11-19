"""
GPS Location Verification System Forms

Forms for GPS zones and location verification requests.
"""

from django import forms
from decimal import Decimal
from .models import GeofenceDefinition, LocationVerification


class GPSZoneForm(forms.ModelForm):
    """Form for creating/editing GPS geofence zones."""

    class Meta:
        model = GeofenceDefinition
        fields = ['name', 'geofence_type', 'description', 'shape',
                  'center_latitude', 'center_longitude', 'radius_meters',
                  'address', 'location', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Main Warehouse, Production Floor A',
            }),
            'geofence_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this location zone',
            }),
            'shape': forms.Select(attrs={
                'class': 'form-control',
            }),
            'center_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 25.276987',
                'step': '0.000001',
            }),
            'center_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 55.296249',
                'step': '0.000001',
            }),
            'radius_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 100',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full address of this location',
            }),
            'location': forms.Select(attrs={
                'class': 'form-control',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        help_texts = {
            'name': 'Unique name for this GPS zone',
            'geofence_type': 'Type of location',
            'shape': 'Currently only circle is supported',
            'center_latitude': 'GPS latitude of zone center (decimal degrees)',
            'center_longitude': 'GPS longitude of zone center (decimal degrees)',
            'radius_meters': 'Geofence radius in meters (default: 100m)',
            'address': 'Physical address (optional)',
            'location': 'Link to inventory location (optional)',
            'is_active': 'Is this zone currently active?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # For now, only support circle shape
        self.fields['shape'].initial = 'CIRCLE'
        self.fields['shape'].widget = forms.HiddenInput()

        # Make coordinates required for circle
        self.fields['center_latitude'].required = True
        self.fields['center_longitude'].required = True
        self.fields['radius_meters'].required = True

    def clean(self):
        cleaned_data = super().clean()
        shape = cleaned_data.get('shape')
        center_lat = cleaned_data.get('center_latitude')
        center_lon = cleaned_data.get('center_longitude')
        radius = cleaned_data.get('radius_meters')

        if shape == 'CIRCLE':
            if not center_lat or not center_lon:
                raise forms.ValidationError(
                    'Center latitude and longitude are required for circle geofence'
                )
            if not radius:
                raise forms.ValidationError(
                    'Radius is required for circle geofence'
                )

            # Validate latitude range (-90 to 90)
            if center_lat and (center_lat < -90 or center_lat > 90):
                raise forms.ValidationError({
                    'center_latitude': 'Latitude must be between -90 and 90 degrees'
                })

            # Validate longitude range (-180 to 180)
            if center_lon and (center_lon < -180 or center_lon > 180):
                raise forms.ValidationError({
                    'center_longitude': 'Longitude must be between -180 and 180 degrees'
                })

            # Validate radius
            if radius and radius < 1:
                raise forms.ValidationError({
                    'radius_meters': 'Radius must be at least 1 meter'
                })

        return cleaned_data


class VerificationRequestForm(forms.ModelForm):
    """Form for creating location verification requests."""

    class Meta:
        model = LocationVerification
        fields = ['verification_type', 'expected_latitude', 'expected_longitude',
                  'expected_address', 'geofence_radius_meters', 'notes']
        widgets = {
            'verification_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'expected_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 25.276987',
                'step': '0.000001',
            }),
            'expected_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 55.296249',
                'step': '0.000001',
            }),
            'expected_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected address/location',
            }),
            'geofence_radius_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '100',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this verification',
            }),
        }
        help_texts = {
            'verification_type': 'Type of verification being performed',
            'expected_latitude': 'Expected GPS latitude',
            'expected_longitude': 'Expected GPS longitude',
            'expected_address': 'Expected address (optional)',
            'geofence_radius_meters': 'How close does the actual location need to be? (meters)',
            'notes': 'Any additional notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make coordinates required
        self.fields['expected_latitude'].required = True
        self.fields['expected_longitude'].required = True

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('expected_latitude')
        longitude = cleaned_data.get('expected_longitude')
        radius = cleaned_data.get('geofence_radius_meters')

        # Validate latitude range
        if latitude and (latitude < -90 or latitude > 90):
            raise forms.ValidationError({
                'expected_latitude': 'Latitude must be between -90 and 90 degrees'
            })

        # Validate longitude range
        if longitude and (longitude < -180 or longitude > 180):
            raise forms.ValidationError({
                'expected_longitude': 'Longitude must be between -180 and 180 degrees'
            })

        # Validate radius
        if radius and radius < 1:
            raise forms.ValidationError({
                'geofence_radius_meters': 'Radius must be at least 1 meter'
            })

        return cleaned_data


class LocationVerifyForm(forms.Form):
    """Form for verifying actual GPS location."""

    actual_latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Actual GPS latitude',
            'step': '0.000001',
        }),
        help_text='Current GPS latitude'
    )

    actual_longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Actual GPS longitude',
            'step': '0.000001',
        }),
        help_text='Current GPS longitude'
    )

    accuracy_meters = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'GPS accuracy (meters)',
        }),
        help_text='GPS accuracy from device (optional)'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any notes about this verification',
        }),
        help_text='Optional notes'
    )

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('actual_latitude')
        longitude = cleaned_data.get('actual_longitude')

        # Validate latitude range
        if latitude and (latitude < -90 or latitude > 90):
            raise forms.ValidationError({
                'actual_latitude': 'Latitude must be between -90 and 90 degrees'
            })

        # Validate longitude range
        if longitude and (longitude < -180 or longitude > 180):
            raise forms.ValidationError({
                'actual_longitude': 'Longitude must be between -180 and 180 degrees'
            })

        return cleaned_data


class VerificationOverrideForm(forms.Form):
    """Form for overriding failed location verifications."""

    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explain why you are overriding this location verification...',
        }),
        help_text='Reason for overriding the failed verification (required)'
    )

    def clean_reason(self):
        reason = self.cleaned_data.get('reason')
        if not reason or len(reason.strip()) < 10:
            raise forms.ValidationError(
                'Please provide a detailed reason (at least 10 characters)'
            )
        return reason

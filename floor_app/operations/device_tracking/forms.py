"""
Employee Device Tracking System Forms

Forms for device registration and check-in/out.
"""

from django import forms
from .models import EmployeeDevice, EmployeePresence


class DeviceRegistrationForm(forms.ModelForm):
    """Form for registering employee devices."""

    class Meta:
        model = EmployeeDevice
        fields = ['employee', 'device_id', 'device_name', 'device_type',
                  'device_model', 'os_version', 'app_version']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-control',
            }),
            'device_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique device ID (IMEI, UUID, etc.)',
            }),
            'device_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., "Ahmed\'s iPhone" or "Production Floor Tablet 1"',
            }),
            'device_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'device_model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., iPhone 13 Pro, Samsung Galaxy S21',
            }),
            'os_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., iOS 16.0, Android 12',
            }),
            'app_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1.0.5',
            }),
        }
        help_texts = {
            'device_id': 'Unique identifier for this device (cannot be changed later)',
            'device_name': 'User-friendly name to identify this device',
            'device_type': 'Type of device',
            'device_model': 'Device model/make',
            'os_version': 'Operating system version',
            'app_version': 'Version of the mobile app installed',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make employee field readonly if editing existing device
        if self.instance and self.instance.pk:
            self.fields['employee'].disabled = True
            self.fields['device_id'].disabled = True

        # Make device_name required
        self.fields['device_name'].required = True

    def clean_device_id(self):
        device_id = self.cleaned_data.get('device_id')

        # Check if device_id already exists (only for new devices)
        if not self.instance.pk:
            if EmployeeDevice.objects.filter(device_id=device_id).exists():
                raise forms.ValidationError(
                    'A device with this ID is already registered'
                )

        return device_id

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class CheckInForm(forms.Form):
    """Form for employee check-in."""

    location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your location (e.g., Production Floor A, Office)',
        }),
        help_text='Where are you checking in from?'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any notes or comments (optional)',
        }),
        help_text='Optional notes for this check-in'
    )

    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )

    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        # If one GPS coordinate is provided, both should be provided
        if (latitude and not longitude) or (longitude and not latitude):
            raise forms.ValidationError(
                'Both latitude and longitude must be provided together'
            )

        return cleaned_data


class CheckOutForm(forms.Form):
    """Form for employee check-out."""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any notes or comments (optional)',
        }),
        help_text='Optional notes for this check-out'
    )

    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )

    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )


class DeviceUpdateForm(forms.ModelForm):
    """Form for updating device settings."""

    class Meta:
        model = EmployeeDevice
        fields = ['device_name', 'is_primary_device', 'is_trusted',
                  'push_enabled', 'device_model', 'os_version', 'app_version']
        widgets = {
            'device_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'is_primary_device': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_trusted': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'push_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'device_model': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'os_version': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'app_version': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'is_primary_device': 'Mark this as your primary device',
            'is_trusted': 'Allow this device for sensitive operations',
            'push_enabled': 'Receive push notifications on this device',
        }


class PresenceVerificationForm(forms.ModelForm):
    """Form for verifying employee presence by supervisor."""

    class Meta:
        model = EmployeePresence
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add verification notes',
            }),
        }
        help_texts = {
            'status': 'Verify the employee presence status',
            'notes': 'Add any notes about this verification',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make status required
        self.fields['status'].required = True

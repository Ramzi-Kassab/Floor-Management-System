"""
Forms for Core app including Django Auth system management
"""
from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserCreateForm(forms.ModelForm):
    """Form for creating new users"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter a strong password'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password again for verification'
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select groups for this user'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'groups']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'is_staff': 'Designates whether the user can log into this admin site.',
            'is_active': 'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        }

    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        """Validate that the two password entries match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")

        # Validate password strength
        if password1:
            validate_password(password1)

        return password2

    def save(self, commit=True):
        """Save user with hashed password"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            self.save_m2m()  # Save groups

        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users"""
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select groups for this user'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'groups']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'is_staff': 'Designates whether the user can log into this admin site.',
            'is_active': 'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.all()

    def clean_email(self):
        """Validate email is unique (excluding current user)"""
        email = self.cleaned_data.get('email')
        if email:
            users = User.objects.filter(email=email).exclude(pk=self.instance.pk)
            if users.exists():
                raise ValidationError('A user with this email already exists.')
        return email


class UserPasswordChangeForm(forms.Form):
    """Form for changing user password (admin-initiated)"""
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter a strong password'
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password again for verification'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        """Validate that the two password entries match"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")

        # Validate password strength
        if password1:
            validate_password(password1, self.user)

        return password2

    def save(self, commit=True):
        """Save the new password"""
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class GroupForm(forms.ModelForm):
    """Form for creating/updating groups"""
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select permissions for this group'
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group name'}),
        }
        help_texts = {
            'name': 'Required. Unique name for this group.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.all()

    def clean_name(self):
        """Validate group name is unique"""
        name = self.cleaned_data.get('name')
        if self.instance and self.instance.pk:
            # Updating existing group
            if Group.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError('A group with this name already exists.')
        else:
            # Creating new group
            if Group.objects.filter(name=name).exists():
                raise ValidationError('A group with this name already exists.')
        return name


class UserPermissionsForm(forms.ModelForm):
    """Form for managing user-specific permissions (not inherited from groups)"""
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select specific permissions for this user'
    )

    class Meta:
        model = User
        fields = ['user_permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['user_permissions'].initial = self.instance.user_permissions.all()

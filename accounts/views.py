"""
Account management views
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


@login_required
def profile(request):
    """
    Display user profile
    """
    context = {
        'page_title': 'My Profile',
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """
    Edit user profile
    """
    if request.method == 'POST':
        # Update user fields
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('account_profile')

    context = {
        'page_title': 'Edit Profile',
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def settings(request):
    """
    User settings page
    """
    context = {
        'page_title': 'Settings',
    }
    return render(request, 'accounts/settings.html', context)


@login_required
def change_password(request):
    """
    Change password view
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('account_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'page_title': 'Change Password',
    }
    return render(request, 'accounts/change_password.html', context)

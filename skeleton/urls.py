"""
URL configuration for skeleton app.

Handles:
- Authentication (login, logout, password change/reset)
- Landing page
- Main dashboard
- Account/profile
- Global search
- Notifications
"""
from django.urls import path
from . import views

app_name = 'skeleton'

urlpatterns = [
    # Landing page & Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Password Change
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),

    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Account
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/settings/', views.account_settings, name='account_settings'),

    # Search & Notifications
    path('search/', views.global_search, name='global_search'),
    path('notifications/', views.notifications_list, name='notifications_list'),
]

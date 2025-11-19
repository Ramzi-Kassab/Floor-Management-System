"""
Vendor Portal System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'vendor_portal'

urlpatterns = [
    # Vendor Management
    path('', views.vendor_dashboard, name='vendor_dashboard'),
    path('register/', views.vendor_registration, name='vendor_registration'),

    # Orders
    path('orders/', views.vendor_orders, name='vendor_orders'),
]

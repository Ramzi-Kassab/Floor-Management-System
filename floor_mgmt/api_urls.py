"""
Central API URL Configuration with Swagger Documentation

This module provides a centralized API routing with automatic
Swagger/OpenAPI documentation using drf-spectacular.
"""
from django.urls import path, include
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # === API Schema & Documentation ===
    # OpenAPI 3.0 schema
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),

    # Swagger UI - Interactive API documentation
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),

    # ReDoc - Alternative API documentation
    path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),

    # === Module APIs ===
    # HR & Employee Management API
    path('hr/', include('floor_app.operations.hr.api.urls')),

    # Additional module APIs can be added here
    # path('inventory/', include('floor_app.operations.inventory.api.urls')),
    # path('production/', include('floor_app.operations.production.api.urls')),
    # path('quality/', include('floor_app.operations.quality.api.urls')),
]

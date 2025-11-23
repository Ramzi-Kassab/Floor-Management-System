"""
Engineering URL Configuration
"""
from django.urls import path
from . import views

app_name = 'engineering'

urlpatterns = [
    # Dashboard
    path('', views.engineering_dashboard, name='dashboard'),

    # Bit Designs
    path('bit-designs/', views.BitDesignListView.as_view(), name='bit_design_list'),
    path('bit-designs/create/', views.BitDesignCreateView.as_view(), name='bit_design_create'),
    path('bit-designs/<int:pk>/', views.BitDesignDetailView.as_view(), name='bit_design_detail'),
    path('bit-designs/<int:pk>/edit/', views.BitDesignUpdateView.as_view(), name='bit_design_edit'),

    # Bit Design Revisions
    path('revisions/', views.BitDesignRevisionListView.as_view(), name='revision_list'),
    path('revisions/create/', views.BitDesignRevisionCreateView.as_view(), name='revision_create'),
    path('revisions/<int:pk>/', views.BitDesignRevisionDetailView.as_view(), name='revision_detail'),

    # BOMs
    path('boms/', views.BOMListView.as_view(), name='bom_list'),
    path('boms/create/', views.BOMCreateView.as_view(), name='bom_create'),
    path('boms/<int:pk>/', views.BOMDetailView.as_view(), name='bom_detail'),
    path('boms/<int:pk>/edit/', views.BOMUpdateView.as_view(), name='bom_edit'),

    # Roller Cone Designs
    path('roller-cone/', views.RollerConeDesignListView.as_view(), name='roller_cone_list'),
    path('roller-cone/create/', views.RollerConeDesignCreateView.as_view(), name='roller_cone_create'),
    path('roller-cone/<int:pk>/', views.RollerConeDesignDetailView.as_view(), name='roller_cone_detail'),
]

"""
Sales, Lifecycle & Drilling Operations - URL Configuration
"""
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Dashboard
    path('', views.SalesDashboardView.as_view(), name='dashboard'),

    # Customer Management
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),

    # Rig Management
    path('rigs/', views.RigListView.as_view(), name='rig_list'),
    path('rigs/create/', views.RigCreateView.as_view(), name='rig_create'),
    path('rigs/<int:pk>/', views.RigDetailView.as_view(), name='rig_detail'),
    path('rigs/<int:pk>/edit/', views.RigUpdateView.as_view(), name='rig_update'),

    # Well Management
    path('wells/', views.WellListView.as_view(), name='well_list'),
    path('wells/create/', views.WellCreateView.as_view(), name='well_create'),
    path('wells/<int:pk>/', views.WellDetailView.as_view(), name='well_detail'),
    path('wells/<int:pk>/edit/', views.WellUpdateView.as_view(), name='well_update'),

    # Sales Opportunities
    path('opportunities/', views.SalesOpportunityListView.as_view(), name='opportunity_list'),
    path('opportunities/create/', views.SalesOpportunityCreateView.as_view(), name='opportunity_create'),
    path('opportunities/<int:pk>/', views.SalesOpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.SalesOpportunityUpdateView.as_view(), name='opportunity_update'),

    # Sales Orders
    path('orders/', views.SalesOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.SalesOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', views.SalesOrderUpdateView.as_view(), name='order_update'),

    # Bit Lifecycle
    path('lifecycle/timeline/', views.BitLifecycleTimelineView.as_view(), name='lifecycle_timeline'),
    path('lifecycle/fleet/', views.BitFleetView.as_view(), name='lifecycle_fleet'),
    path('lifecycle/events/create/', views.BitLifecycleEventCreateView.as_view(), name='lifecycle_event_create'),

    # Drilling Runs
    path('drilling/', views.DrillingRunListView.as_view(), name='drilling_list'),
    path('drilling/create/', views.DrillingRunCreateView.as_view(), name='drilling_create'),
    path('drilling/<int:pk>/', views.DrillingRunDetailView.as_view(), name='drilling_detail'),
    path('drilling/<int:pk>/edit/', views.DrillingRunUpdateView.as_view(), name='drilling_update'),

    # Dull Grade Evaluations
    path('dullgrades/', views.DullGradeEvaluationListView.as_view(), name='dullgrade_list'),
    path('dullgrades/create/', views.DullGradeEvaluationCreateView.as_view(), name='dullgrade_create'),
    path('dullgrades/<int:pk>/', views.DullGradeEvaluationDetailView.as_view(), name='dullgrade_detail'),
    path('dullgrades/<int:pk>/edit/', views.DullGradeEvaluationUpdateView.as_view(), name='dullgrade_update'),

    # Shipments
    path('shipments/', views.ShipmentListView.as_view(), name='shipment_list'),
    path('shipments/create/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('shipments/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('shipments/<int:pk>/edit/', views.ShipmentUpdateView.as_view(), name='shipment_update'),

    # Junk Sales
    path('junksales/', views.JunkSaleListView.as_view(), name='junksale_list'),
    path('junksales/create/', views.JunkSaleCreateView.as_view(), name='junksale_create'),
    path('junksales/<int:pk>/', views.JunkSaleDetailView.as_view(), name='junksale_detail'),
    path('junksales/<int:pk>/edit/', views.JunkSaleUpdateView.as_view(), name='junksale_update'),

    # Reports
    path('reports/', views.SalesReportsDashboardView.as_view(), name='reports_dashboard'),
]

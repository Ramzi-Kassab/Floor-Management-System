from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Item Master CRUD
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_edit'),

    # Bit Designs
    path('bit-designs/', views.BitDesignListView.as_view(), name='bitdesign_list'),
    path('bit-designs/<int:pk>/', views.BitDesignDetailView.as_view(), name='bitdesign_detail'),

    # MAT Revisions
    path('mats/', views.BitDesignRevisionListView.as_view(), name='mat_list'),
    path('mats/<int:pk>/', views.BitDesignRevisionDetailView.as_view(), name='mat_detail'),

    # Serial Units
    path('serial-units/', views.SerialUnitListView.as_view(), name='serialunit_list'),
    path('serial-units/create/', views.SerialUnitCreateView.as_view(), name='serialunit_create'),
    path('serial-units/create/', views.SerialUnitCreateView.as_view(), name='serial_unit_create'),  # Alias
    path('serial-units/<int:pk>/', views.SerialUnitDetailView.as_view(), name='serialunit_detail'),
    path('serial-units/<int:pk>/edit/', views.SerialUnitUpdateView.as_view(), name='serialunit_edit'),

    # Inventory Stock
    path('stock/', views.InventoryStockListView.as_view(), name='stock_list'),
    path('stock/<int:pk>/', views.InventoryStockDetailView.as_view(), name='stock_detail'),
    path('stock/adjust/', views.stock_adjustment, name='stock_adjust'),
    path('stock/adjust/create/', views.stock_adjustment, name='stock_adjustment_create'),  # Alias

    # BOMs
    path('boms/', views.BOMListView.as_view(), name='bom_list'),
    path('boms/create/', views.BOMCreateView.as_view(), name='bom_create'),
    path('boms/<int:pk>/', views.BOMDetailView.as_view(), name='bom_detail'),
    path('boms/<int:pk>/edit/', views.BOMUpdateView.as_view(), name='bom_edit'),

    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),

    # Settings / Reference Data
    path('settings/', views.settings_dashboard, name='settings'),
    path('settings/', views.settings_dashboard, name='settings_dashboard'),  # Alias
    path('settings/conditions/', views.ConditionTypeListView.as_view(), name='condition_list'),
    path('settings/ownership/', views.OwnershipTypeListView.as_view(), name='ownership_list'),
    path('settings/categories/', views.ItemCategoryListView.as_view(), name='category_list'),
    path('settings/locations/', views.LocationListView.as_view(), name='location_list'),
    path('settings/uom/', views.UOMListView.as_view(), name='uom_list'),
]

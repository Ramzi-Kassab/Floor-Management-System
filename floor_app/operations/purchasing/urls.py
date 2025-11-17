"""
Purchasing & Logistics URL Configuration
"""

from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # ========== Supplier Management ==========
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),

    # ========== Purchase Requisition ==========
    path('pr/', views.PRListView.as_view(), name='pr_list'),
    path('pr/create/', views.PRCreateView.as_view(), name='pr_create'),
    path('pr/<int:pk>/', views.PRDetailView.as_view(), name='pr_detail'),
    path('pr/<int:pk>/submit/', views.pr_submit, name='pr_submit'),
    path('pr/<int:pk>/approve/', views.pr_approve, name='pr_approve'),

    # ========== Purchase Order ==========
    path('po/', views.POListView.as_view(), name='po_list'),
    path('po/create/', views.POCreateView.as_view(), name='po_create'),
    path('po/<int:pk>/', views.PODetailView.as_view(), name='po_detail'),
    path('po/<int:pk>/submit/', views.po_submit, name='po_submit'),
    path('po/<int:pk>/approve/', views.po_approve, name='po_approve'),
    path('po/<int:pk>/send/', views.po_send, name='po_send'),

    # ========== Goods Receipt Note ==========
    path('grn/', views.GRNListView.as_view(), name='grn_list'),
    path('grn/create/', views.GRNCreateView.as_view(), name='grn_create'),
    path('grn/<int:pk>/', views.GRNDetailView.as_view(), name='grn_detail'),
    path('grn/<int:pk>/post/', views.grn_post, name='grn_post'),

    # ========== Supplier Invoice ==========
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/match/', views.invoice_three_way_match, name='invoice_match'),

    # ========== Internal Transfers ==========
    path('transfers/', views.TransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.TransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.TransferDetailView.as_view(), name='transfer_detail'),

    # ========== Outbound Shipments ==========
    path('shipments/', views.ShipmentListView.as_view(), name='shipment_list'),
    path('shipments/create/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('shipments/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('shipments/<int:pk>/confirm-delivery/', views.shipment_confirm_delivery, name='shipment_confirm_delivery'),

    # ========== Customer Returns ==========
    path('customer-returns/', views.CustomerReturnListView.as_view(), name='customer_return_list'),
    path('customer-returns/create/', views.CustomerReturnCreateView.as_view(), name='customer_return_create'),
    path('customer-returns/<int:pk>/', views.CustomerReturnDetailView.as_view(), name='customer_return_detail'),

    # ========== API Endpoints ==========
    path('api/suppliers/search/', views.api_supplier_search, name='api_supplier_search'),
    path('api/po/search/', views.api_po_search, name='api_po_search'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]

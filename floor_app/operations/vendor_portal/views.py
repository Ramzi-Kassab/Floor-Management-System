"""
Vendor Portal System Views

Template-rendering views for vendor registration, orders, and management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import (
    Vendor,
    VendorContact,
    VendorOrder,
    VendorInvoice,
    VendorDocument,
    VendorRating,
)


@login_required
def vendor_dashboard(request):
    """
    Vendor portal dashboard.

    Shows:
    - Vendor overview
    - Recent orders
    - Pending invoices
    - Statistics
    """
    try:
        # Get all active vendors
        vendors = Vendor.objects.filter(is_active=True).annotate(
            order_count=Count('orders'),
            total_orders_value=Sum('orders__total_amount')
        )

        # Recent orders
        recent_orders = VendorOrder.objects.select_related(
            'vendor',
            'created_by'
        ).order_by('-order_date')[:10]

        # Pending invoices
        pending_invoices = VendorInvoice.objects.filter(
            status='PENDING'
        ).select_related('vendor', 'order').order_by('-invoice_date')[:10]

        # Statistics
        stats = {
            'total_vendors': Vendor.objects.count(),
            'active_vendors': Vendor.objects.filter(is_active=True).count(),
            'total_orders': VendorOrder.objects.count(),
            'pending_orders': VendorOrder.objects.filter(status='PENDING').count(),
            'pending_invoices': VendorInvoice.objects.filter(status='PENDING').count(),
            'total_orders_value': VendorOrder.objects.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
        }

        context = {
            'vendors': vendors,
            'recent_orders': recent_orders,
            'pending_invoices': pending_invoices,
            'stats': stats,
            'page_title': 'Vendor Portal',
        }

    except Exception as e:
        messages.error(request, f'Error loading vendor dashboard: {str(e)}')
        context = {
            'vendors': [],
            'recent_orders': [],
            'pending_invoices': [],
            'stats': {},
            'page_title': 'Vendor Portal',
        }

    return render(request, 'vendor_portal/vendor_dashboard.html', context)


@login_required
def vendor_registration(request):
    """
    Register new vendor.

    Handles:
    - Vendor information
    - Contact details
    - Banking information
    - Document upload
    """
    try:
        if request.method == 'POST':
            try:
                vendor_name = request.POST.get('vendor_name')
                vendor_code = request.POST.get('vendor_code')
                vendor_type = request.POST.get('vendor_type')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                tax_id = request.POST.get('tax_id', '')
                payment_terms = request.POST.get('payment_terms', '30')

                if not all([vendor_name, vendor_code, vendor_type, email, phone]):
                    messages.error(request, 'Please fill in all required fields.')
                else:
                    # Check if vendor code already exists
                    if Vendor.objects.filter(vendor_code=vendor_code).exists():
                        messages.error(request, 'Vendor code already exists.')
                    else:
                        vendor = Vendor.objects.create(
                            vendor_name=vendor_name,
                            vendor_code=vendor_code,
                            vendor_type=vendor_type,
                            email=email,
                            phone=phone,
                            address=address,
                            tax_id=tax_id,
                            payment_terms_days=int(payment_terms),
                            registered_by=request.user,
                            is_active=True
                        )

                        # Create primary contact
                        contact_name = request.POST.get('contact_name')
                        contact_email = request.POST.get('contact_email')
                        contact_phone = request.POST.get('contact_phone')

                        if contact_name:
                            VendorContact.objects.create(
                                vendor=vendor,
                                contact_name=contact_name,
                                email=contact_email or email,
                                phone=contact_phone or phone,
                                is_primary=True
                            )

                        messages.success(request, f'Vendor "{vendor_name}" registered successfully.')
                        return redirect('vendor_portal:vendor_dashboard')

            except Exception as e:
                messages.error(request, f'Error registering vendor: {str(e)}')

        # Vendor types
        vendor_types = Vendor.VENDOR_TYPES

        context = {
            'vendor_types': vendor_types,
            'page_title': 'Register Vendor',
        }

    except Exception as e:
        messages.error(request, f'Error loading registration form: {str(e)}')
        context = {
            'vendor_types': [],
            'page_title': 'Register Vendor',
        }

    return render(request, 'vendor_portal/vendor_registration.html', context)


@login_required
def vendor_orders(request):
    """
    View and manage vendor orders.

    Shows:
    - All vendor orders
    - Filter by vendor, status, date
    - Order details
    """
    try:
        orders = VendorOrder.objects.select_related(
            'vendor',
            'created_by'
        ).order_by('-order_date')

        # Filter by vendor
        vendor_id = request.GET.get('vendor')
        if vendor_id:
            orders = orders.filter(vendor_id=vendor_id)

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)

        # Filter by date range
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if from_date:
            orders = orders.filter(order_date__gte=from_date)
        if to_date:
            orders = orders.filter(order_date__lte=to_date)

        # Search
        search_query = request.GET.get('q')
        if search_query:
            orders = orders.filter(
                Q(order_number__icontains=search_query) |
                Q(vendor__vendor_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Get all vendors for filter
        vendors = Vendor.objects.filter(is_active=True).order_by('vendor_name')

        # Statistics
        stats = {
            'total_orders': VendorOrder.objects.count(),
            'pending': VendorOrder.objects.filter(status='PENDING').count(),
            'confirmed': VendorOrder.objects.filter(status='CONFIRMED').count(),
            'delivered': VendorOrder.objects.filter(status='DELIVERED').count(),
            'total_value': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        }

        context = {
            'orders': orders,
            'vendors': vendors,
            'stats': stats,
            'status_choices': VendorOrder.STATUS_CHOICES,
            'vendor_filter': vendor_id,
            'status_filter': status_filter,
            'search_query': search_query,
            'page_title': 'Vendor Orders',
        }

    except Exception as e:
        messages.error(request, f'Error loading vendor orders: {str(e)}')
        context = {
            'orders': [],
            'vendors': [],
            'stats': {},
            'page_title': 'Vendor Orders',
        }

    return render(request, 'vendor_portal/vendor_orders.html', context)

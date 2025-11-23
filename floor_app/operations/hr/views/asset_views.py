"""
HR Asset Management Views

Views for managing company assets, asset types, and asset assignments.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
import csv
import base64
from io import BytesIO

from ..models import AssetType, HRAsset, AssetAssignment, HREmployee
from ..decorators import hr_manager_required
from ..utils.qr_utils import generate_asset_qr_image


# ============================================================================
# ASSET TYPE MANAGEMENT
# ============================================================================

class AssetTypeListView(ListView):
    """List all asset types."""
    model = AssetType
    template_name = 'hr/assets/type_list.html'
    context_object_name = 'asset_types'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetType.objects.annotate(
            asset_count=Count('assets')
        ).order_by('category', 'name')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(category__icontains=search)
            )

        # Active/Inactive filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total_types': AssetType.objects.count(),
            'active_types': AssetType.objects.filter(is_active=True).count(),
            'total_assets': HRAsset.objects.count(),
        }
        return context


class AssetTypeCreateView(CreateView):
    """Create a new asset type."""
    model = AssetType
    template_name = 'hr/assets/type_form.html'
    fields = [
        'code', 'name', 'description', 'category',
        'requires_serial_number', 'requires_maintenance',
        'maintenance_interval_days', 'depreciation_period_months',
        'is_active'
    ]

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Asset type created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:asset_type_list')


class AssetTypeUpdateView(UpdateView):
    """Update an existing asset type."""
    model = AssetType
    template_name = 'hr/assets/type_form.html'
    fields = [
        'code', 'name', 'description', 'category',
        'requires_serial_number', 'requires_maintenance',
        'maintenance_interval_days', 'depreciation_period_months',
        'is_active'
    ]

    def form_valid(self, form):
        messages.success(self, 'Asset type updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:asset_type_list')


# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

class AssetListView(ListView):
    """List all assets."""
    model = HRAsset
    template_name = 'hr/assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get_queryset(self):
        queryset = HRAsset.objects.select_related(
            'asset_type',
            'cost_center',
            'currency',
            'created_by'
        ).order_by('-created_at')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_tag__icontains=search) |
                Q(name__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(model__icontains=search)
            )

        # Asset type filter
        asset_type = self.request.GET.get('asset_type')
        if asset_type:
            queryset = queryset.filter(asset_type_id=asset_type)

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Condition filter
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)

        # Available filter
        available = self.request.GET.get('available')
        if available == '1':
            queryset = queryset.filter(status='available')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset_types'] = AssetType.objects.filter(is_active=True)
        context['stats'] = {
            'total_assets': HRAsset.objects.count(),
            'available': HRAsset.objects.filter(status='available').count(),
            'assigned': HRAsset.objects.filter(status='assigned').count(),
            'maintenance': HRAsset.objects.filter(status='in_maintenance').count(),
            'needs_maintenance': HRAsset.objects.filter(
                next_maintenance_date__lte=timezone.now().date()
            ).count(),
        }
        return context


class AssetDetailView(DetailView):
    """View asset details."""
    model = HRAsset
    template_name = 'hr/assets/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return HRAsset.objects.select_related(
            'asset_type',
            'cost_center',
            'currency',
            'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        # Get assignment history
        context['assignments'] = AssetAssignment.objects.filter(
            asset=asset
        ).select_related(
            'employee__person',
            'assigned_by',
            'returned_by'
        ).order_by('-assignment_date')

        # Get current assignment
        try:
            context['current_assignment'] = AssetAssignment.objects.get(
                asset=asset,
                status='active'
            )
        except AssetAssignment.DoesNotExist:
            context['current_assignment'] = None

        # Generate QR code for asset
        asset_qr_code = None
        try:
            qr_image = generate_asset_qr_image(asset)
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            asset_qr_code = base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            # Log error but don't fail the view
            print(f"Error generating asset QR code: {e}")

        context['asset_qr_code'] = asset_qr_code

        return context


class AssetCreateView(CreateView):
    """Create a new asset."""
    model = HRAsset
    template_name = 'hr/assets/asset_form.html'
    fields = [
        'asset_type', 'name', 'serial_number',
        'manufacturer', 'model', 'specifications',
        'purchase_date', 'purchase_cost', 'currency', 'supplier',
        'warranty_expiry_date',
        'status', 'condition', 'current_location', 'cost_center',
        'notes'
    ]

    def get_initial(self):
        initial = super().get_initial()

        # Pre-fill asset type if provided
        asset_type_id = self.request.GET.get('asset_type')
        if asset_type_id:
            try:
                asset_type = AssetType.objects.get(pk=asset_type_id)
                initial['asset_type'] = asset_type
            except AssetType.DoesNotExist:
                pass

        initial['status'] = 'available'
        initial['condition'] = 'good'

        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Asset created successfully. Asset Tag: {form.instance.asset_tag}')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:asset_detail', kwargs={'pk': self.object.pk})


class AssetUpdateView(UpdateView):
    """Update an existing asset."""
    model = HRAsset
    template_name = 'hr/assets/asset_form.html'
    fields = [
        'asset_type', 'name', 'serial_number',
        'manufacturer', 'model', 'specifications',
        'purchase_date', 'purchase_cost', 'currency', 'supplier',
        'warranty_expiry_date',
        'status', 'condition', 'current_location', 'cost_center',
        'last_maintenance_date', 'next_maintenance_date',
        'notes'
    ]

    def form_valid(self, form):
        messages.success(self.request, 'Asset updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:asset_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# ASSET ASSIGNMENT MANAGEMENT
# ============================================================================

class AssetAssignmentListView(ListView):
    """List all asset assignments."""
    model = AssetAssignment
    template_name = 'hr/assets/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 25

    def get_queryset(self):
        queryset = AssetAssignment.objects.select_related(
            'asset__asset_type',
            'employee__person',
            'employee__department',
            'assigned_by'
        ).order_by('-assignment_date')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset__asset_tag__icontains=search) |
                Q(asset__name__icontains=search) |
                Q(employee__employee_code__icontains=search) |
                Q(employee__person__first_name__icontains=search) |
                Q(employee__person__last_name__icontains=search)
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Employee filter
        employee = self.request.GET.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total_assignments': AssetAssignment.objects.count(),
            'active_assignments': AssetAssignment.objects.filter(status='active').count(),
            'returned': AssetAssignment.objects.filter(status='returned').count(),
            'overdue': AssetAssignment.objects.filter(
                status='active',
                expected_return_date__lt=timezone.now().date()
            ).count(),
        }
        return context


class AssetAssignmentDetailView(DetailView):
    """View asset assignment details."""
    model = AssetAssignment
    template_name = 'hr/assets/assignment_detail.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        return AssetAssignment.objects.select_related(
            'asset__asset_type',
            'employee__person',
            'employee__department',
            'employee__position',
            'assigned_by',
            'returned_by'
        )


class AssetAssignmentCreateView(CreateView):
    """Create a new asset assignment."""
    model = AssetAssignment
    template_name = 'hr/assets/assignment_form.html'
    fields = [
        'asset', 'employee',
        'assignment_date', 'expected_return_date',
        'condition_at_assignment',
        'assignment_notes',
        'employee_acknowledged'
    ]

    def get_initial(self):
        initial = super().get_initial()

        # Pre-fill asset if provided
        asset_id = self.request.GET.get('asset')
        if asset_id:
            try:
                asset = HRAsset.objects.get(pk=asset_id)
                initial['asset'] = asset
                initial['condition_at_assignment'] = asset.condition
            except HRAsset.DoesNotExist:
                pass

        # Pre-fill employee if provided
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = HREmployee.objects.get(pk=employee_id)
                initial['employee'] = employee
            except HREmployee.DoesNotExist:
                pass

        initial['assignment_date'] = timezone.now().date()

        return initial

    def form_valid(self, form):
        try:
            form.instance.assigned_by = self.request.user
            form.instance.status = 'active'
            # Validate before saving
            form.instance.clean()
            messages.success(self.request, 'Asset assigned successfully.')
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('hr:asset_assignment_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# ASSET ASSIGNMENT ACTIONS
# ============================================================================

@login_required
@hr_manager_required
def return_asset(request, pk):
    """Return an asset from assignment."""
    assignment = get_object_or_404(AssetAssignment, pk=pk)

    if not assignment.is_active:
        messages.warning(request, 'This assignment is not active.')
        return redirect('hr:asset_assignment_detail', pk=assignment.pk)

    if request.method == 'POST':
        return_date = request.POST.get('actual_return_date')
        condition = request.POST.get('condition_at_return')
        notes = request.POST.get('return_notes', '')

        assignment.actual_return_date = return_date
        assignment.condition_at_return = condition
        assignment.return_notes = notes
        assignment.status = 'returned'
        assignment.returned_by = request.user
        assignment.save()

        # Update asset status
        assignment.asset.status = 'available'
        assignment.asset.condition = condition
        assignment.asset.save()

        messages.success(request, 'Asset returned successfully.')
        return redirect('hr:asset_assignment_detail', pk=assignment.pk)

    context = {
        'assignment': assignment,
        'suggested_return_date': timezone.now().date(),
        'condition_choices': HRAsset.CONDITION_CHOICES,
    }

    return render(request, 'hr/assets/return_asset.html', context)


# ============================================================================
# ASSET DASHBOARD & REPORTS
# ============================================================================

@login_required
@hr_manager_required
def asset_dashboard(request):
    """Asset management dashboard."""
    today = timezone.now().date()

    # Statistics
    stats = {
        'total_assets': HRAsset.objects.count(),
        'available': HRAsset.objects.filter(status='available').count(),
        'assigned': HRAsset.objects.filter(status='assigned').count(),
        'in_maintenance': HRAsset.objects.filter(status='in_maintenance').count(),
        'needs_maintenance': HRAsset.objects.filter(
            next_maintenance_date__lte=today
        ).count(),
        'warranty_expiring': HRAsset.objects.filter(
            warranty_expiry_date__gte=today,
            warranty_expiry_date__lte=today + timezone.timedelta(days=90)
        ).count(),
    }

    # Assets by type
    assets_by_type = {}
    for asset_type in AssetType.objects.filter(is_active=True):
        count = HRAsset.objects.filter(asset_type=asset_type).count()
        if count > 0:
            assets_by_type[asset_type.name] = count

    # Assets needing maintenance
    maintenance_needed = HRAsset.objects.filter(
        next_maintenance_date__lte=today
    ).select_related('asset_type')[:10]

    # Recent assignments
    recent_assignments = AssetAssignment.objects.select_related(
        'asset',
        'employee__person'
    ).order_by('-assignment_date')[:10]

    # Overdue returns
    overdue_returns = AssetAssignment.objects.filter(
        status='active',
        expected_return_date__lt=today
    ).select_related(
        'asset',
        'employee__person'
    ).order_by('expected_return_date')[:10]

    context = {
        'stats': stats,
        'assets_by_type': assets_by_type,
        'maintenance_needed': maintenance_needed,
        'recent_assignments': recent_assignments,
        'overdue_returns': overdue_returns,
    }

    return render(request, 'hr/assets/dashboard.html', context)


@login_required
@hr_manager_required
def export_assets_csv(request):
    """Export assets to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Asset Tag', 'Name', 'Type', 'Serial Number',
        'Manufacturer', 'Model', 'Status', 'Condition',
        'Purchase Date', 'Purchase Cost', 'Location'
    ])

    assets = HRAsset.objects.select_related('asset_type').order_by('asset_tag')

    for asset in assets:
        writer.writerow([
            asset.asset_tag,
            asset.name,
            asset.asset_type.name,
            asset.serial_number,
            asset.manufacturer,
            asset.model,
            asset.get_status_display(),
            asset.get_condition_display(),
            asset.purchase_date or '',
            asset.purchase_cost or '',
            asset.current_location,
        ])

    return response


# ============================================================================
# API ENDPOINTS
# ============================================================================

@login_required
def asset_search_api(request):
    """API endpoint for asset search."""
    query = request.GET.get('q', '')
    available_only = request.GET.get('available_only') == '1'

    assets = HRAsset.objects.select_related('asset_type')

    if query:
        assets = assets.filter(
            Q(asset_tag__icontains=query) |
            Q(name__icontains=query) |
            Q(serial_number__icontains=query)
        )

    if available_only:
        assets = assets.filter(status='available')

    data = []
    for asset in assets[:20]:  # Limit to 20 results
        data.append({
            'id': asset.pk,
            'asset_tag': asset.asset_tag,
            'name': asset.name,
            'type': asset.asset_type.name,
            'status': asset.status,
            'condition': asset.condition,
            'is_available': asset.is_available,
        })

    return JsonResponse({'assets': data})


@login_required
def employee_assets_api(request, employee_id):
    """Get all assets assigned to an employee."""
    assignments = AssetAssignment.objects.filter(
        employee_id=employee_id,
        status='active'
    ).select_related('asset__asset_type')

    data = []
    for assignment in assignments:
        data.append({
            'id': assignment.pk,
            'asset_tag': assignment.asset.asset_tag,
            'asset_name': assignment.asset.name,
            'asset_type': assignment.asset.asset_type.name,
            'assignment_date': assignment.assignment_date.isoformat(),
            'expected_return_date': assignment.expected_return_date.isoformat() if assignment.expected_return_date else None,
            'is_overdue': assignment.is_overdue,
        })

    return JsonResponse({'assignments': data})

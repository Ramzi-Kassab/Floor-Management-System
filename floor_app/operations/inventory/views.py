from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, F
from django.core.paginator import Paginator

from .models import (
    Item, ItemCategory, ConditionType, OwnershipType, UnitOfMeasure,
    BitDesign, BitDesignRevision, BitDesignLevel, BitDesignType,
    SerialUnit, InventoryStock, Location,
    BOMHeader, BOMLine,
    InventoryTransaction,
)
from .forms import ItemForm, SerialUnitForm, BOMHeaderForm, TransactionForm, StockAdjustmentForm


# ============================================================================
# DASHBOARD
# ============================================================================
@login_required
def dashboard(request):
    """Main inventory dashboard with summary statistics."""
    context = {
        'total_items': Item.objects.filter(is_active=True).count(),
        'total_serial_units': SerialUnit.objects.exclude(status='SCRAPPED').count(),
        'total_categories': ItemCategory.objects.filter(is_active=True).count(),
        'total_locations': Location.objects.filter(is_active=True).count(),

        # Stock alerts
        'low_stock_count': InventoryStock.objects.filter(
            quantity_on_hand__lte=F('reorder_point')
        ).count(),

        # Serial unit status breakdown
        'bits_in_stock': SerialUnit.objects.filter(status='IN_STOCK').count(),
        'bits_at_rig': SerialUnit.objects.filter(status='AT_RIG').count(),
        'bits_under_repair': SerialUnit.objects.filter(status='UNDER_REPAIR').count(),

        # Recent transactions
        'recent_transactions': InventoryTransaction.objects.select_related(
            'item', 'serial_unit'
        ).order_by('-transaction_date')[:10],

        # Low stock items
        'low_stock_items': InventoryStock.objects.filter(
            quantity_on_hand__lte=F('reorder_point')
        ).select_related('item', 'location', 'condition', 'ownership')[:10],

        # Critical serial units
        'critical_units': SerialUnit.objects.filter(
            status__in=['UNDER_INSPECTION', 'UNDER_REPAIR']
        ).select_related('item', 'location', 'condition')[:10],
    }
    return render(request, 'inventory/dashboard.html', context)


# ============================================================================
# ITEM MASTER CRUD
# ============================================================================
class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'inventory/items/list.html'
    context_object_name = 'items'
    paginate_by = 25

    def get_queryset(self):
        qs = Item.objects.select_related('category', 'uom', 'bit_design_revision').filter(is_deleted=False)

        # Search
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(sku__icontains=search) | Q(name__icontains=search))

        # Category filter
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)

        # Active filter
        active = self.request.GET.get('active')
        if active == 'yes':
            qs = qs.filter(is_active=True)
        elif active == 'no':
            qs = qs.filter(is_active=False)

        return qs.order_by('sku')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ItemCategory.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_active'] = self.request.GET.get('active', '')
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'inventory/items/detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object

        if item.is_serialized:
            context['serial_units'] = item.serial_units.select_related(
                'location', 'condition', 'ownership'
            )[:20]
        else:
            context['stock_records'] = item.inventory_stocks.select_related(
                'location', 'condition', 'ownership'
            )

        context['bom_usages'] = item.bom_usages.select_related('bom_header')[:10]
        context['recent_transactions'] = InventoryTransaction.objects.filter(
            item=item
        ).order_by('-transaction_date')[:10]

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'inventory/items/form.html'
    success_url = reverse_lazy('inventory:item_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Item {form.instance.sku} created successfully.')
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'inventory/items/form.html'

    def get_success_url(self):
        return reverse_lazy('inventory:item_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Item {form.instance.sku} updated successfully.')
        return super().form_valid(form)


# ============================================================================
# BIT DESIGN / MAT VIEWS
# ============================================================================
class BitDesignListView(LoginRequiredMixin, ListView):
    model = BitDesign
    template_name = 'inventory/bit_designs/list.html'
    context_object_name = 'designs'
    paginate_by = 25

    def get_queryset(self):
        qs = BitDesign.objects.select_related('level').filter(is_deleted=False)

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(design_code__icontains=search) | Q(name__icontains=search))

        level = self.request.GET.get('level')
        if level:
            qs = qs.filter(level_id=level)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = BitDesignLevel.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['selected_level'] = self.request.GET.get('level', '')
        return context


class BitDesignDetailView(LoginRequiredMixin, DetailView):
    model = BitDesign
    template_name = 'inventory/bit_designs/detail.html'
    context_object_name = 'design'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revisions'] = self.object.revisions.select_related('design_type').order_by('-created_at')
        return context


class BitDesignRevisionListView(LoginRequiredMixin, ListView):
    model = BitDesignRevision
    template_name = 'inventory/bit_designs/mat_list.html'
    context_object_name = 'mats'
    paginate_by = 25

    def get_queryset(self):
        qs = BitDesignRevision.objects.select_related(
            'bit_design', 'bit_design__level', 'design_type'
        ).filter(is_deleted=False)

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(mat_number__icontains=search) | Q(bit_design__design_code__icontains=search))

        active = self.request.GET.get('active')
        if active == 'yes':
            qs = qs.filter(is_active=True)
        elif active == 'no':
            qs = qs.filter(is_active=False)

        temporary = self.request.GET.get('temporary')
        if temporary == 'yes':
            qs = qs.filter(is_temporary=True)
        elif temporary == 'no':
            qs = qs.filter(is_temporary=False)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_active'] = self.request.GET.get('active', '')
        context['selected_temporary'] = self.request.GET.get('temporary', '')
        return context


class BitDesignRevisionDetailView(LoginRequiredMixin, DetailView):
    model = BitDesignRevision
    template_name = 'inventory/bit_designs/mat_detail.html'
    context_object_name = 'mat'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['boms'] = self.object.boms.filter(is_active=True)
        context['serial_units'] = SerialUnit.objects.filter(current_mat=self.object)[:20]
        return context


# ============================================================================
# SERIAL UNIT CRUD
# ============================================================================
class SerialUnitListView(LoginRequiredMixin, ListView):
    model = SerialUnit
    template_name = 'inventory/serial_units/list.html'
    context_object_name = 'units'
    paginate_by = 25

    def get_queryset(self):
        qs = SerialUnit.objects.select_related(
            'item', 'current_mat', 'location', 'condition', 'ownership'
        ).filter(is_deleted=False)

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(serial_number__icontains=search) | Q(item__sku__icontains=search))

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        ownership = self.request.GET.get('ownership')
        if ownership:
            qs = qs.filter(ownership_id=ownership)

        location = self.request.GET.get('location')
        if location:
            qs = qs.filter(location_id=location)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = SerialUnit.STATUS_CHOICES
        context['ownership_types'] = OwnershipType.objects.filter(is_active=True)
        context['locations'] = Location.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_ownership'] = self.request.GET.get('ownership', '')
        context['selected_location'] = self.request.GET.get('location', '')
        return context


class SerialUnitDetailView(LoginRequiredMixin, DetailView):
    model = SerialUnit
    template_name = 'inventory/serial_units/detail.html'
    context_object_name = 'unit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mat_history'] = self.object.mat_history.select_related(
            'old_mat', 'new_mat'
        ).order_by('-changed_at')[:10]
        context['transactions'] = InventoryTransaction.objects.filter(
            serial_unit=self.object
        ).order_by('-transaction_date')[:20]
        return context


class SerialUnitCreateView(LoginRequiredMixin, CreateView):
    model = SerialUnit
    form_class = SerialUnitForm
    template_name = 'inventory/serial_units/form.html'
    success_url = reverse_lazy('inventory:serialunit_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Serial unit {form.instance.serial_number} created.')
        return super().form_valid(form)


class SerialUnitUpdateView(LoginRequiredMixin, UpdateView):
    model = SerialUnit
    form_class = SerialUnitForm
    template_name = 'inventory/serial_units/form.html'

    def get_success_url(self):
        return reverse_lazy('inventory:serialunit_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Serial unit {form.instance.serial_number} updated.')
        return super().form_valid(form)


# ============================================================================
# INVENTORY STOCK
# ============================================================================
class InventoryStockListView(LoginRequiredMixin, ListView):
    model = InventoryStock
    template_name = 'inventory/stock/list.html'
    context_object_name = 'stocks'
    paginate_by = 25

    def get_queryset(self):
        qs = InventoryStock.objects.select_related('item', 'location', 'condition', 'ownership')

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(item__sku__icontains=search) | Q(item__name__icontains=search))

        condition = self.request.GET.get('condition')
        if condition:
            qs = qs.filter(condition_id=condition)

        ownership = self.request.GET.get('ownership')
        if ownership:
            qs = qs.filter(ownership_id=ownership)

        low_stock = self.request.GET.get('low_stock')
        if low_stock == 'yes':
            qs = qs.filter(quantity_on_hand__lte=F('reorder_point'))

        return qs.order_by('item__sku')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conditions'] = ConditionType.objects.filter(is_active=True)
        context['ownership_types'] = OwnershipType.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['selected_condition'] = self.request.GET.get('condition', '')
        context['selected_ownership'] = self.request.GET.get('ownership', '')
        context['selected_low_stock'] = self.request.GET.get('low_stock', '')
        return context


class InventoryStockDetailView(LoginRequiredMixin, DetailView):
    model = InventoryStock
    template_name = 'inventory/stock/detail.html'
    context_object_name = 'stock'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = InventoryTransaction.objects.filter(
            item=self.object.item,
            to_location=self.object.location
        ).order_by('-transaction_date')[:20]
        return context


@login_required
def stock_adjustment(request):
    """Manual stock adjustment form."""
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            # Create adjustment transaction
            txn = InventoryTransaction.objects.create(
                transaction_type='ADJUSTMENT',
                item=form.cleaned_data['item'],
                quantity=form.cleaned_data['quantity'],
                uom=form.cleaned_data['item'].uom,
                to_location=form.cleaned_data['location'],
                to_condition=form.cleaned_data['condition'],
                to_ownership=form.cleaned_data['ownership'],
                reason_code=form.cleaned_data['reason'],
                notes=form.cleaned_data['notes'],
                created_by=request.user,
            )

            # Update stock record
            stock, created = InventoryStock.objects.get_or_create(
                item=form.cleaned_data['item'],
                location=form.cleaned_data['location'],
                condition=form.cleaned_data['condition'],
                ownership=form.cleaned_data['ownership'],
                defaults={'quantity_on_hand': 0}
            )
            stock.adjust_quantity(form.cleaned_data['quantity'], request.user)

            messages.success(request, f'Stock adjustment recorded: {txn.transaction_number}')
            return redirect('inventory:stock_list')
    else:
        form = StockAdjustmentForm()

    return render(request, 'inventory/stock/adjustment_form.html', {'form': form})


# ============================================================================
# BOM VIEWS
# ============================================================================
class BOMListView(LoginRequiredMixin, ListView):
    model = BOMHeader
    template_name = 'inventory/boms/list.html'
    context_object_name = 'boms'
    paginate_by = 25

    def get_queryset(self):
        qs = BOMHeader.objects.select_related('target_mat').filter(is_deleted=False)

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(bom_number__icontains=search) | Q(name__icontains=search))

        bom_type = self.request.GET.get('type')
        if bom_type:
            qs = qs.filter(bom_type=bom_type)

        active = self.request.GET.get('active')
        if active == 'yes':
            qs = qs.filter(is_active=True)
        elif active == 'no':
            qs = qs.filter(is_active=False)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bom_types'] = BOMHeader.BOM_TYPE_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_active'] = self.request.GET.get('active', '')
        return context


class BOMDetailView(LoginRequiredMixin, DetailView):
    model = BOMHeader
    template_name = 'inventory/boms/detail.html'
    context_object_name = 'bom'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.select_related(
            'component_item', 'uom', 'required_condition', 'required_ownership'
        ).order_by('line_number')
        return context


class BOMCreateView(LoginRequiredMixin, CreateView):
    model = BOMHeader
    form_class = BOMHeaderForm
    template_name = 'inventory/boms/form.html'
    success_url = reverse_lazy('inventory:bom_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'BOM {form.instance.bom_number} created.')
        return super().form_valid(form)


class BOMUpdateView(LoginRequiredMixin, UpdateView):
    model = BOMHeader
    form_class = BOMHeaderForm
    template_name = 'inventory/boms/form.html'

    def get_success_url(self):
        return reverse_lazy('inventory:bom_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'BOM {form.instance.bom_number} updated.')
        return super().form_valid(form)


# ============================================================================
# TRANSACTIONS
# ============================================================================
class TransactionListView(LoginRequiredMixin, ListView):
    model = InventoryTransaction
    template_name = 'inventory/transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 50

    def get_queryset(self):
        qs = InventoryTransaction.objects.select_related(
            'item', 'serial_unit', 'from_location', 'to_location'
        )

        txn_type = self.request.GET.get('type')
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)

        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(transaction_number__icontains=search) |
                Q(item__sku__icontains=search) |
                Q(serial_unit__serial_number__icontains=search)
            )

        return qs.order_by('-transaction_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction_types'] = InventoryTransaction.TRANSACTION_TYPE_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['selected_type'] = self.request.GET.get('type', '')
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = InventoryTransaction
    template_name = 'inventory/transactions/detail.html'
    context_object_name = 'transaction'


@login_required
def transaction_create(request):
    """Create a manual inventory transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.created_by = request.user
            txn.save()
            messages.success(request, f'Transaction {txn.transaction_number} created.')
            return redirect('inventory:transaction_list')
    else:
        form = TransactionForm()

    return render(request, 'inventory/transactions/form.html', {'form': form})


# ============================================================================
# SETTINGS / REFERENCE DATA
# ============================================================================
@login_required
def settings_dashboard(request):
    """Settings overview page."""
    context = {
        'condition_count': ConditionType.objects.filter(is_active=True).count(),
        'ownership_count': OwnershipType.objects.filter(is_active=True).count(),
        'category_count': ItemCategory.objects.filter(is_active=True).count(),
        'location_count': Location.objects.filter(is_active=True).count(),
        'uom_count': UnitOfMeasure.objects.filter(is_active=True).count(),
    }
    return render(request, 'inventory/settings/dashboard.html', context)


class ConditionTypeListView(LoginRequiredMixin, ListView):
    model = ConditionType
    template_name = 'inventory/settings/condition_list.html'
    context_object_name = 'conditions'


class OwnershipTypeListView(LoginRequiredMixin, ListView):
    model = OwnershipType
    template_name = 'inventory/settings/ownership_list.html'
    context_object_name = 'ownerships'


class ItemCategoryListView(LoginRequiredMixin, ListView):
    model = ItemCategory
    template_name = 'inventory/settings/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ItemCategory.objects.filter(is_deleted=False).order_by('sort_order', 'code')


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'inventory/settings/location_list.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return Location.objects.filter(is_deleted=False).order_by('code')


class UOMListView(LoginRequiredMixin, ListView):
    model = UnitOfMeasure
    template_name = 'inventory/settings/uom_list.html'
    context_object_name = 'uoms'

    def get_queryset(self):
        return UnitOfMeasure.objects.filter(is_active=True).order_by('code')

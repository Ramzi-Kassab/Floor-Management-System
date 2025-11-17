"""
Sales, Lifecycle & Drilling Operations - Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Sum, Avg, Q, F, Max
from django.utils import timezone
from datetime import timedelta
from .models import (
    Customer, Rig, Well,
    SalesOpportunity, SalesOrder, SalesOrderLine,
    DrillingRun,
    DullGradeEvaluation,
    BitLifecycleEvent, Shipment, JunkSale,
)
from .forms import (
    CustomerForm, RigForm, WellForm,
    SalesOpportunityForm, SalesOrderForm, SalesOrderLineForm,
    DrillingRunForm,
    DullGradeEvaluationForm,
    BitLifecycleEventForm, ShipmentForm, JunkSaleForm,
    BitLifecycleSearchForm, DrillingRunSearchForm,
)


# ============================================================================
# Dashboard
# ============================================================================

class SalesDashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard for Sales & Lifecycle module."""
    template_name = 'sales/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Customer Statistics
        context['customer_stats'] = {
            'total_active': Customer.objects.filter(
                is_deleted=False, account_status='ACTIVE'
            ).count(),
            'total_operators': Customer.objects.filter(
                is_deleted=False, customer_type='OPERATOR'
            ).count(),
        }

        # Sales Pipeline
        open_statuses = ['IDENTIFIED', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION']
        opportunities = SalesOpportunity.objects.filter(
            is_deleted=False, status__in=open_statuses
        )
        context['pipeline_stats'] = {
            'total_opportunities': opportunities.count(),
            'total_value': opportunities.aggregate(
                total=Sum('estimated_value')
            )['total'] or 0,
            'weighted_value': sum(opp.weighted_value for opp in opportunities),
        }

        # Sales Orders
        pending_statuses = ['DRAFT', 'CONFIRMED', 'IN_PRODUCTION', 'READY_TO_SHIP']
        orders = SalesOrder.objects.filter(
            is_deleted=False, status__in=pending_statuses
        )
        overdue_orders = [o for o in orders if o.is_overdue]
        context['order_stats'] = {
            'pending_orders': orders.count(),
            'overdue_orders': len(overdue_orders),
            'total_value': orders.aggregate(total=Sum('total_value'))['total'] or 0,
        }

        # Drilling Operations
        active_runs = DrillingRun.objects.filter(
            is_deleted=False, status='IN_PROGRESS'
        ).count()
        recent_runs = DrillingRun.objects.filter(
            is_deleted=False, run_out_date__gte=timezone.now() - timedelta(days=30)
        )
        context['drilling_stats'] = {
            'active_runs': active_runs,
            'runs_last_30_days': recent_runs.count(),
            'avg_rop': recent_runs.aggregate(avg=Avg('avg_rop'))['avg'] or 0,
            'total_footage': recent_runs.aggregate(
                total=Sum('footage_drilled')
            )['total'] or 0,
        }

        # Recent Items
        context['recent_opportunities'] = SalesOpportunity.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well').order_by('-created_at')[:5]

        context['recent_orders'] = SalesOrder.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well').order_by('-order_date')[:5]

        context['recent_runs'] = DrillingRun.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well', 'rig').order_by('-run_in_date')[:5]

        context['recent_dull_grades'] = DullGradeEvaluation.objects.filter(
            is_deleted=False
        ).select_related('customer').order_by('-evaluation_date')[:5]

        # Shipments Due
        context['shipments_pending'] = Shipment.objects.filter(
            is_deleted=False, status__in=['PENDING', 'SHIPPED', 'IN_TRANSIT']
        ).order_by('expected_delivery_date')[:5]

        return context


# ============================================================================
# Customer Management Views
# ============================================================================

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'sales/customer/list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        qs = Customer.objects.filter(is_deleted=False)
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(customer_code__icontains=search) |
                Q(name__icontains=search) |
                Q(legal_name__icontains=search)
            )
        customer_type = self.request.GET.get('type', '')
        if customer_type:
            qs = qs.filter(customer_type=customer_type)
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(account_status=status)
        return qs.order_by('name')


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'sales/customer/detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        # Related data
        context['rigs'] = Rig.objects.filter(
            is_deleted=False, owner_customer=customer
        )
        context['wells'] = Well.objects.filter(
            is_deleted=False, operator_customer=customer
        )
        context['opportunities'] = SalesOpportunity.objects.filter(
            is_deleted=False, customer=customer
        ).order_by('-created_at')[:10]
        context['orders'] = SalesOrder.objects.filter(
            is_deleted=False, customer=customer
        ).order_by('-order_date')[:10]
        context['runs'] = DrillingRun.objects.filter(
            is_deleted=False, customer=customer
        ).order_by('-run_in_date')[:10]
        context['lifecycle_events'] = BitLifecycleEvent.objects.filter(
            is_deleted=False, customer=customer
        ).order_by('-event_datetime')[:20]

        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'sales/customer/form.html'
    success_url = reverse_lazy('sales:customer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer created successfully.')
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'sales/customer/form.html'

    def get_success_url(self):
        return reverse('sales:customer_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Rig Views
# ============================================================================

class RigListView(LoginRequiredMixin, ListView):
    model = Rig
    template_name = 'sales/rig/list.html'
    context_object_name = 'rigs'
    paginate_by = 20

    def get_queryset(self):
        qs = Rig.objects.filter(is_deleted=False).select_related('owner_customer')
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(rig_code__icontains=search) | Q(name__icontains=search)
            )
        return qs.order_by('name')


class RigDetailView(LoginRequiredMixin, DetailView):
    model = Rig
    template_name = 'sales/rig/detail.html'
    context_object_name = 'rig'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rig = self.object
        context['wells'] = Well.objects.filter(is_deleted=False, current_rig=rig)
        context['runs'] = DrillingRun.objects.filter(
            is_deleted=False, rig=rig
        ).order_by('-run_in_date')[:20]
        context['shipments'] = Shipment.objects.filter(
            is_deleted=False, to_rig=rig
        ).order_by('-ship_date')[:10]
        return context


class RigCreateView(LoginRequiredMixin, CreateView):
    model = Rig
    form_class = RigForm
    template_name = 'sales/rig/form.html'
    success_url = reverse_lazy('sales:rig_list')

    def form_valid(self, form):
        messages.success(self.request, 'Rig created successfully.')
        return super().form_valid(form)


class RigUpdateView(LoginRequiredMixin, UpdateView):
    model = Rig
    form_class = RigForm
    template_name = 'sales/rig/form.html'

    def get_success_url(self):
        return reverse('sales:rig_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Rig updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Well Views
# ============================================================================

class WellListView(LoginRequiredMixin, ListView):
    model = Well
    template_name = 'sales/well/list.html'
    context_object_name = 'wells'
    paginate_by = 20

    def get_queryset(self):
        qs = Well.objects.filter(is_deleted=False).select_related(
            'operator_customer', 'current_rig'
        )
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(well_name__icontains=search) |
                Q(field_name__icontains=search) |
                Q(uwi__icontains=search)
            )
        return qs.order_by('well_name')


class WellDetailView(LoginRequiredMixin, DetailView):
    model = Well
    template_name = 'sales/well/detail.html'
    context_object_name = 'well'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        well = self.object
        context['runs'] = DrillingRun.objects.filter(
            is_deleted=False, well=well
        ).order_by('-run_in_date')
        context['dull_grades'] = DullGradeEvaluation.objects.filter(
            is_deleted=False, well=well
        ).order_by('-evaluation_date')
        return context


class WellCreateView(LoginRequiredMixin, CreateView):
    model = Well
    form_class = WellForm
    template_name = 'sales/well/form.html'
    success_url = reverse_lazy('sales:well_list')

    def form_valid(self, form):
        messages.success(self.request, 'Well created successfully.')
        return super().form_valid(form)


class WellUpdateView(LoginRequiredMixin, UpdateView):
    model = Well
    form_class = WellForm
    template_name = 'sales/well/form.html'

    def get_success_url(self):
        return reverse('sales:well_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Well updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Sales Opportunity Views
# ============================================================================

class SalesOpportunityListView(LoginRequiredMixin, ListView):
    model = SalesOpportunity
    template_name = 'sales/opportunity/list.html'
    context_object_name = 'opportunities'
    paginate_by = 20

    def get_queryset(self):
        qs = SalesOpportunity.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well', 'rig')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pipeline summary
        open_statuses = ['IDENTIFIED', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION']
        opps = SalesOpportunity.objects.filter(
            is_deleted=False, status__in=open_statuses
        )
        context['pipeline_total'] = opps.aggregate(
            total=Sum('estimated_value')
        )['total'] or 0
        context['pipeline_weighted'] = sum(o.weighted_value for o in opps)
        return context


class SalesOpportunityDetailView(LoginRequiredMixin, DetailView):
    model = SalesOpportunity
    template_name = 'sales/opportunity/detail.html'
    context_object_name = 'opportunity'


class SalesOpportunityCreateView(LoginRequiredMixin, CreateView):
    model = SalesOpportunity
    form_class = SalesOpportunityForm
    template_name = 'sales/opportunity/form.html'
    success_url = reverse_lazy('sales:opportunity_list')

    def form_valid(self, form):
        form.instance.opportunity_number = SalesOpportunity.generate_opportunity_number()
        messages.success(self.request, 'Sales opportunity created successfully.')
        return super().form_valid(form)


class SalesOpportunityUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesOpportunity
    form_class = SalesOpportunityForm
    template_name = 'sales/opportunity/form.html'

    def get_success_url(self):
        return reverse('sales:opportunity_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Sales opportunity updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Sales Order Views
# ============================================================================

class SalesOrderListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'sales/order/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = SalesOrder.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well', 'rig')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-order_date')


class SalesOrderDetailView(LoginRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'sales/order/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.filter(is_deleted=False)
        return context


class SalesOrderCreateView(LoginRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/order/form.html'
    success_url = reverse_lazy('sales:order_list')

    def form_valid(self, form):
        form.instance.order_number = SalesOrder.generate_order_number()
        messages.success(self.request, 'Sales order created successfully.')
        return super().form_valid(form)


class SalesOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/order/form.html'

    def get_success_url(self):
        return reverse('sales:order_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Sales order updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Bit Lifecycle Views
# ============================================================================

class BitLifecycleTimelineView(LoginRequiredMixin, TemplateView):
    """Timeline view for a single bit's lifecycle history."""
    template_name = 'sales/lifecycle/timeline.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bit_serial = self.request.GET.get('bit_serial', '')

        if bit_serial:
            events = BitLifecycleEvent.objects.filter(
                is_deleted=False, bit_serial_number=bit_serial
            ).order_by('event_datetime')
            context['events'] = events
            context['bit_serial'] = bit_serial

            # Summary stats
            if events.exists():
                latest = events.last()
                context['latest_event'] = latest
                context['total_events'] = events.count()

                # Get drilling runs
                runs = DrillingRun.objects.filter(
                    is_deleted=False, bit_serial_number=bit_serial
                ).order_by('run_sequence')
                context['runs'] = runs
                context['total_footage'] = runs.aggregate(
                    total=Sum('footage_drilled')
                )['total'] or 0
                context['total_hours'] = runs.aggregate(
                    total=Sum('hours_on_bottom')
                )['total'] or 0

                # Get dull grades
                dull_grades = DullGradeEvaluation.objects.filter(
                    is_deleted=False, bit_serial_number=bit_serial
                ).order_by('run_sequence')
                context['dull_grades'] = dull_grades

        context['search_form'] = BitLifecycleSearchForm(self.request.GET)
        return context


class BitFleetView(LoginRequiredMixin, TemplateView):
    """Fleet view showing all bits by customer/rig with status."""
    template_name = 'sales/lifecycle/fleet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get unique bits from lifecycle events (most recent status)
        # This is a simplified view - in production, query SerialUnit directly
        latest_events = BitLifecycleEvent.objects.filter(
            is_deleted=False
        ).values('bit_serial_number').annotate(
            last_event=Max('event_datetime')
        )

        bits_info = []
        for entry in latest_events[:100]:  # Limit for performance
            bit_sn = entry['bit_serial_number']
            last_event = BitLifecycleEvent.objects.filter(
                is_deleted=False,
                bit_serial_number=bit_sn,
                event_datetime=entry['last_event']
            ).first()

            if last_event:
                runs = DrillingRun.objects.filter(
                    is_deleted=False, bit_serial_number=bit_sn
                )
                bits_info.append({
                    'serial_number': bit_sn,
                    'mat_number': last_event.mat_number,
                    'current_status': last_event.new_status or last_event.event_type,
                    'current_location': last_event.new_location or last_event.location_description,
                    'customer': last_event.customer,
                    'rig': last_event.rig,
                    'last_event': last_event,
                    'total_runs': runs.count(),
                    'total_footage': runs.aggregate(
                        total=Sum('footage_drilled')
                    )['total'] or 0,
                })

        context['bits'] = bits_info

        # Group by customer
        customer_groups = {}
        for bit in bits_info:
            cust = bit['customer']
            if cust:
                if cust not in customer_groups:
                    customer_groups[cust] = []
                customer_groups[cust].append(bit)
        context['customer_groups'] = customer_groups

        return context


class BitLifecycleEventCreateView(LoginRequiredMixin, CreateView):
    model = BitLifecycleEvent
    form_class = BitLifecycleEventForm
    template_name = 'sales/lifecycle/event_form.html'

    def form_valid(self, form):
        form.instance.event_number = BitLifecycleEvent.generate_event_number()
        if not form.instance.recorded_by:
            form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Lifecycle event recorded successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        bit_sn = self.object.bit_serial_number
        return reverse('sales:lifecycle_timeline') + f'?bit_serial={bit_sn}'


# ============================================================================
# Drilling Run Views
# ============================================================================

class DrillingRunListView(LoginRequiredMixin, ListView):
    model = DrillingRun
    template_name = 'sales/drilling/list.html'
    context_object_name = 'runs'
    paginate_by = 20

    def get_queryset(self):
        qs = DrillingRun.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well', 'rig')

        # Apply filters
        form = DrillingRunSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('bit_serial_number'):
                qs = qs.filter(
                    bit_serial_number__icontains=form.cleaned_data['bit_serial_number']
                )
            if form.cleaned_data.get('customer'):
                qs = qs.filter(customer=form.cleaned_data['customer'])
            if form.cleaned_data.get('well'):
                qs = qs.filter(well=form.cleaned_data['well'])
            if form.cleaned_data.get('rig'):
                qs = qs.filter(rig=form.cleaned_data['rig'])
            if form.cleaned_data.get('status'):
                qs = qs.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(run_in_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(run_in_date__lte=form.cleaned_data['date_to'])

        return qs.order_by('-run_in_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DrillingRunSearchForm(self.request.GET)
        return context


class DrillingRunDetailView(LoginRequiredMixin, DetailView):
    model = DrillingRun
    template_name = 'sales/drilling/detail.html'
    context_object_name = 'run'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        run = self.object

        # Get associated dull grade
        if run.dull_grade_id:
            context['dull_grade'] = DullGradeEvaluation.objects.filter(
                id=run.dull_grade_id
            ).first()

        # Other runs for same bit
        context['other_runs'] = DrillingRun.objects.filter(
            is_deleted=False,
            bit_serial_number=run.bit_serial_number
        ).exclude(pk=run.pk).order_by('run_sequence')

        return context


class DrillingRunCreateView(LoginRequiredMixin, CreateView):
    model = DrillingRun
    form_class = DrillingRunForm
    template_name = 'sales/drilling/form.html'
    success_url = reverse_lazy('sales:drilling_list')

    def form_valid(self, form):
        form.instance.run_number = DrillingRun.generate_run_number()
        messages.success(self.request, 'Drilling run recorded successfully.')
        return super().form_valid(form)


class DrillingRunUpdateView(LoginRequiredMixin, UpdateView):
    model = DrillingRun
    form_class = DrillingRunForm
    template_name = 'sales/drilling/form.html'

    def get_success_url(self):
        return reverse('sales:drilling_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Drilling run updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Dull Grade Evaluation Views
# ============================================================================

class DullGradeEvaluationListView(LoginRequiredMixin, ListView):
    model = DullGradeEvaluation
    template_name = 'sales/dullgrade/list.html'
    context_object_name = 'evaluations'
    paginate_by = 20

    def get_queryset(self):
        qs = DullGradeEvaluation.objects.filter(
            is_deleted=False
        ).select_related('customer', 'well', 'rig')
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(evaluation_number__icontains=search) |
                Q(bit_serial_number__icontains=search) |
                Q(iadc_dull_grade__icontains=search)
            )
        return qs.order_by('-evaluation_date')


class DullGradeEvaluationDetailView(LoginRequiredMixin, DetailView):
    model = DullGradeEvaluation
    template_name = 'sales/dullgrade/detail.html'
    context_object_name = 'evaluation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        eval_obj = self.object

        # Get associated drilling run
        if eval_obj.drilling_run_id:
            context['drilling_run'] = DrillingRun.objects.filter(
                id=eval_obj.drilling_run_id
            ).first()

        # Other evaluations for same bit
        context['other_evaluations'] = DullGradeEvaluation.objects.filter(
            is_deleted=False,
            bit_serial_number=eval_obj.bit_serial_number
        ).exclude(pk=eval_obj.pk).order_by('run_sequence')

        return context


class DullGradeEvaluationCreateView(LoginRequiredMixin, CreateView):
    model = DullGradeEvaluation
    form_class = DullGradeEvaluationForm
    template_name = 'sales/dullgrade/form.html'
    success_url = reverse_lazy('sales:dullgrade_list')

    def form_valid(self, form):
        form.instance.evaluation_number = DullGradeEvaluation.generate_evaluation_number()
        if not form.instance.evaluated_by:
            form.instance.evaluated_by = self.request.user
        messages.success(self.request, 'Dull grade evaluation recorded successfully.')
        return super().form_valid(form)


class DullGradeEvaluationUpdateView(LoginRequiredMixin, UpdateView):
    model = DullGradeEvaluation
    form_class = DullGradeEvaluationForm
    template_name = 'sales/dullgrade/form.html'

    def get_success_url(self):
        return reverse('sales:dullgrade_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Dull grade evaluation updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Shipment Views
# ============================================================================

class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    template_name = 'sales/shipment/list.html'
    context_object_name = 'shipments'
    paginate_by = 20

    def get_queryset(self):
        qs = Shipment.objects.filter(
            is_deleted=False
        ).select_related('to_customer', 'to_rig')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-ship_date')


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    model = Shipment
    template_name = 'sales/shipment/detail.html'
    context_object_name = 'shipment'


class ShipmentCreateView(LoginRequiredMixin, CreateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'sales/shipment/form.html'
    success_url = reverse_lazy('sales:shipment_list')

    def form_valid(self, form):
        form.instance.shipment_number = Shipment.generate_shipment_number()
        messages.success(self.request, 'Shipment created successfully.')
        return super().form_valid(form)


class ShipmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Shipment
    form_class = ShipmentForm
    template_name = 'sales/shipment/form.html'

    def get_success_url(self):
        return reverse('sales:shipment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Shipment updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Junk Sale Views
# ============================================================================

class JunkSaleListView(LoginRequiredMixin, ListView):
    model = JunkSale
    template_name = 'sales/junksale/list.html'
    context_object_name = 'junk_sales'
    paginate_by = 20

    def get_queryset(self):
        return JunkSale.objects.filter(
            is_deleted=False
        ).order_by('-sale_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = JunkSale.objects.filter(is_deleted=False, status='SOLD')
        context['total_weight'] = sales.aggregate(
            total=Sum('net_weight_kg')
        )['total'] or 0
        context['total_value'] = sales.aggregate(
            total=Sum('total_sale_value')
        )['total'] or 0
        return context


class JunkSaleDetailView(LoginRequiredMixin, DetailView):
    model = JunkSale
    template_name = 'sales/junksale/detail.html'
    context_object_name = 'junk_sale'


class JunkSaleCreateView(LoginRequiredMixin, CreateView):
    model = JunkSale
    form_class = JunkSaleForm
    template_name = 'sales/junksale/form.html'
    success_url = reverse_lazy('sales:junksale_list')

    def form_valid(self, form):
        form.instance.junk_sale_number = JunkSale.generate_junk_sale_number()
        messages.success(self.request, 'Junk sale recorded successfully.')
        return super().form_valid(form)


class JunkSaleUpdateView(LoginRequiredMixin, UpdateView):
    model = JunkSale
    form_class = JunkSaleForm
    template_name = 'sales/junksale/form.html'

    def get_success_url(self):
        return reverse('sales:junksale_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Junk sale updated successfully.')
        return super().form_valid(form)


# ============================================================================
# Reports Views
# ============================================================================

class SalesReportsDashboardView(LoginRequiredMixin, TemplateView):
    """Reports and analytics dashboard."""
    template_name = 'sales/reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Performance metrics
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # ROP trends
        recent_runs = DrillingRun.objects.filter(
            is_deleted=False,
            run_out_date__gte=thirty_days_ago
        )
        context['avg_rop_30d'] = recent_runs.aggregate(
            avg=Avg('avg_rop')
        )['avg'] or 0
        context['total_footage_30d'] = recent_runs.aggregate(
            total=Sum('footage_drilled')
        )['total'] or 0

        # Dull grade statistics
        recent_evals = DullGradeEvaluation.objects.filter(
            is_deleted=False,
            evaluation_date__gte=thirty_days_ago
        )
        context['avg_severity'] = sum(
            e.severity_score for e in recent_evals
        ) / max(recent_evals.count(), 1)
        context['rerun_rate'] = sum(
            1 for e in recent_evals if e.is_rerunnable
        ) / max(recent_evals.count(), 1) * 100

        # Top dull characteristics
        char_counts = recent_evals.values(
            'primary_dull_characteristic'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        context['top_dull_chars'] = char_counts

        # Customer performance
        customer_stats = DrillingRun.objects.filter(
            is_deleted=False,
            run_out_date__gte=thirty_days_ago
        ).values('customer__name').annotate(
            total_footage=Sum('footage_drilled'),
            avg_rop=Avg('avg_rop'),
            run_count=Count('id')
        ).order_by('-total_footage')[:10]
        context['customer_performance'] = customer_stats

        return context

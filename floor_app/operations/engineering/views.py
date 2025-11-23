"""
Engineering Views

Views for managing bit designs, BOMs, and engineering specifications.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Prefetch

from .models import (
    BitDesign, BitDesignRevision, BitDesignLevel, BitDesignType,
    BOMHeader, BOMLine,
    RollerConeBitType, RollerConeBearing, RollerConeSeal,
    RollerConeDesign, RollerConeComponent, RollerConeBOM
)


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def engineering_dashboard(request):
    """Engineering dashboard with summary statistics."""
    context = {
        'total_bit_designs': BitDesign.objects.count(),
        'total_revisions': BitDesignRevision.objects.count(),
        'total_boms': BOMHeader.objects.count(),
        'total_roller_cone_designs': RollerConeDesign.objects.count(),

        # Recent activity
        'recent_designs': BitDesign.objects.select_related(
            'design_type', 'design_level'
        ).order_by('-created_at')[:10],

        'recent_revisions': BitDesignRevision.objects.select_related(
            'bit_design'
        ).order_by('-revision_date')[:10],

        'recent_boms': BOMHeader.objects.select_related(
            'bit_design_revision'
        ).order_by('-created_at')[:10],

        # Stats by type
        'designs_by_type': BitDesign.objects.values(
            'design_type__name'
        ).annotate(count=Count('id')).order_by('-count')[:5],

        'designs_by_level': BitDesign.objects.values(
            'design_level__name'
        ).annotate(count=Count('id')).order_by('-count'),
    }
    return render(request, 'engineering/dashboard.html', context)


# ============================================================================
# BIT DESIGN CRUD
# ============================================================================

class BitDesignListView(LoginRequiredMixin, ListView):
    """List all bit designs."""
    model = BitDesign
    template_name = 'engineering/bit_designs/list.html'
    context_object_name = 'designs'
    paginate_by = 25

    def get_queryset(self):
        queryset = BitDesign.objects.select_related(
            'design_type', 'design_level'
        ).prefetch_related(
            'revisions'
        ).order_by('-created_at')

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(design_number__icontains=search) |
                Q(description__icontains=search)
            )

        # Type filter
        design_type = self.request.GET.get('type')
        if design_type:
            queryset = queryset.filter(design_type_id=design_type)

        # Level filter
        design_level = self.request.GET.get('level')
        if design_level:
            queryset = queryset.filter(design_level_id=design_level)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['design_types'] = BitDesignType.objects.all()
        context['design_levels'] = BitDesignLevel.objects.all()
        context['stats'] = {
            'total_designs': BitDesign.objects.count(),
            'total_revisions': BitDesignRevision.objects.count(),
        }
        return context


class BitDesignDetailView(LoginRequiredMixin, DetailView):
    """View bit design details."""
    model = BitDesign
    template_name = 'engineering/bit_designs/detail.html'
    context_object_name = 'design'

    def get_queryset(self):
        return BitDesign.objects.select_related(
            'design_type', 'design_level'
        ).prefetch_related(
            Prefetch('revisions', queryset=BitDesignRevision.objects.order_by('-revision_date'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        design = self.object

        # Get all revisions
        context['revisions'] = design.revisions.all()

        # Get latest revision
        context['latest_revision'] = design.revisions.first()

        # Get BOMs for this design
        context['boms'] = BOMHeader.objects.filter(
            bit_design_revision__bit_design=design
        ).select_related('bit_design_revision')

        return context


class BitDesignCreateView(LoginRequiredMixin, CreateView):
    """Create a new bit design."""
    model = BitDesign
    template_name = 'engineering/bit_designs/form.html'
    fields = ['design_number', 'design_type', 'design_level', 'description', 'specifications']

    def form_valid(self, form):
        messages.success(self.request, 'Bit design created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:bit_design_detail', kwargs={'pk': self.object.pk})


class BitDesignUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing bit design."""
    model = BitDesign
    template_name = 'engineering/bit_designs/form.html'
    fields = ['design_number', 'design_type', 'design_level', 'description', 'specifications']

    def form_valid(self, form):
        messages.success(self.request, 'Bit design updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:bit_design_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# BIT DESIGN REVISION CRUD
# ============================================================================

class BitDesignRevisionListView(LoginRequiredMixin, ListView):
    """List all bit design revisions."""
    model = BitDesignRevision
    template_name = 'engineering/revisions/list.html'
    context_object_name = 'revisions'
    paginate_by = 25

    def get_queryset(self):
        queryset = BitDesignRevision.objects.select_related(
            'bit_design', 'bit_design__design_type'
        ).order_by('-revision_date')

        # Filter by design if provided
        design_id = self.request.GET.get('design')
        if design_id:
            queryset = queryset.filter(bit_design_id=design_id)

        return queryset


class BitDesignRevisionDetailView(LoginRequiredMixin, DetailView):
    """View bit design revision details."""
    model = BitDesignRevision
    template_name = 'engineering/revisions/detail.html'
    context_object_name = 'revision'

    def get_queryset(self):
        return BitDesignRevision.objects.select_related(
            'bit_design', 'bit_design__design_type', 'bit_design__design_level'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revision = self.object

        # Get BOMs for this revision
        context['boms'] = BOMHeader.objects.filter(
            bit_design_revision=revision
        ).prefetch_related('lines')

        return context


class BitDesignRevisionCreateView(LoginRequiredMixin, CreateView):
    """Create a new bit design revision."""
    model = BitDesignRevision
    template_name = 'engineering/revisions/form.html'
    fields = ['bit_design', 'revision_number', 'revision_date', 'description', 'change_notes']

    def get_initial(self):
        initial = super().get_initial()
        design_id = self.request.GET.get('design')
        if design_id:
            initial['bit_design'] = design_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Revision created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:revision_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# BOM CRUD
# ============================================================================

class BOMListView(LoginRequiredMixin, ListView):
    """List all BOMs."""
    model = BOMHeader
    template_name = 'engineering/boms/list.html'
    context_object_name = 'boms'
    paginate_by = 25

    def get_queryset(self):
        queryset = BOMHeader.objects.select_related(
            'bit_design_revision', 'bit_design_revision__bit_design'
        ).annotate(
            line_count=Count('lines')
        ).order_by('-created_at')

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(bom_number__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset


class BOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details."""
    model = BOMHeader
    template_name = 'engineering/boms/detail.html'
    context_object_name = 'bom'

    def get_queryset(self):
        return BOMHeader.objects.select_related(
            'bit_design_revision', 'bit_design_revision__bit_design'
        ).prefetch_related(
            Prefetch('lines', queryset=BOMLine.objects.select_related('item').order_by('line_number'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bom = self.object

        # Calculate total quantities
        total_items = bom.lines.count()

        context['total_items'] = total_items

        return context


class BOMCreateView(LoginRequiredMixin, CreateView):
    """Create a new BOM."""
    model = BOMHeader
    template_name = 'engineering/boms/form.html'
    fields = ['bom_number', 'bit_design_revision', 'description', 'is_active']

    def get_initial(self):
        initial = super().get_initial()
        revision_id = self.request.GET.get('revision')
        if revision_id:
            initial['bit_design_revision'] = revision_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'BOM created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:bom_detail', kwargs={'pk': self.object.pk})


class BOMUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing BOM."""
    model = BOMHeader
    template_name = 'engineering/boms/form.html'
    fields = ['bom_number', 'bit_design_revision', 'description', 'is_active']

    def form_valid(self, form):
        messages.success(self.request, 'BOM updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:bom_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# ROLLER CONE DESIGN CRUD
# ============================================================================

class RollerConeDesignListView(LoginRequiredMixin, ListView):
    """List all roller cone designs."""
    model = RollerConeDesign
    template_name = 'engineering/roller_cone/list.html'
    context_object_name = 'designs'
    paginate_by = 25

    def get_queryset(self):
        queryset = RollerConeDesign.objects.select_related(
            'bit_type'
        ).annotate(
            component_count=Count('components')
        ).order_by('-created_at')

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(design_code__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset


class RollerConeDesignDetailView(LoginRequiredMixin, DetailView):
    """View roller cone design details."""
    model = RollerConeDesign
    template_name = 'engineering/roller_cone/detail.html'
    context_object_name = 'design'

    def get_queryset(self):
        return RollerConeDesign.objects.select_related(
            'bit_type', 'bearing', 'seal'
        ).prefetch_related(
            Prefetch('components', queryset=RollerConeComponent.objects.select_related('item').order_by('sequence'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        design = self.object

        # Get BOMs for this design
        context['boms'] = RollerConeBOM.objects.filter(
            roller_cone_design=design
        ).prefetch_related('items')

        return context


class RollerConeDesignCreateView(LoginRequiredMixin, CreateView):
    """Create a new roller cone design."""
    model = RollerConeDesign
    template_name = 'engineering/roller_cone/form.html'
    fields = ['design_code', 'bit_type', 'bearing', 'seal', 'description', 'specifications']

    def form_valid(self, form):
        messages.success(self.request, 'Roller cone design created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engineering:roller_cone_detail', kwargs={'pk': self.object.pk})

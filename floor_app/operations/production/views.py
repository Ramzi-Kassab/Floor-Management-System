from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from django.http import JsonResponse

from .models import (
    BatchOrder,
    JobCard,
    JobRoute,
    JobRouteStep,
    OperationDefinition,
    CutterSymbol,
    ChecklistTemplate,
    JobCutterEvaluationHeader,
    JobCutterEvaluationDetail,
    ApiThreadInspection,
    NdtReport,
    JobChecklistInstance,
    JobChecklistItem,
)
from .forms import (
    BatchOrderForm,
    JobCardForm,
    RouteStepForm,
    RouteStepCompleteForm,
    CutterEvaluationHeaderForm,
    ApiThreadInspectionForm,
    NdtReportForm,
    ChecklistItemCompleteForm,
)


# ========== Dashboard ==========

@login_required
def dashboard(request):
    """Production dashboard with summary statistics."""

    # Summary stats
    open_batches = BatchOrder.objects.filter(
        status__in=['PLANNED', 'IN_PROGRESS', 'PARTIAL_COMPLETE']
    ).count()

    open_job_cards = JobCard.objects.exclude(
        status__in=['COMPLETE', 'SCRAPPED', 'CANCELLED']
    ).count()

    jobs_in_evaluation = JobCard.objects.filter(
        status='EVALUATION_IN_PROGRESS'
    ).count()

    jobs_awaiting_approval = JobCard.objects.filter(
        status='AWAITING_APPROVAL'
    ).count()

    jobs_in_production = JobCard.objects.filter(
        status='IN_PRODUCTION'
    ).count()

    # Urgent/High priority jobs
    urgent_jobs = JobCard.objects.filter(
        priority__in=['HIGH', 'RUSH', 'CRITICAL'],
        status__in=['NEW', 'EVALUATION_IN_PROGRESS', 'AWAITING_APPROVAL', 'RELEASED_TO_SHOP', 'IN_PRODUCTION']
    ).order_by('-priority', 'planned_end_date')[:10]

    # Overdue jobs
    overdue_jobs = JobCard.objects.filter(
        planned_end_date__lt=timezone.now().date(),
        status__in=['NEW', 'EVALUATION_IN_PROGRESS', 'AWAITING_APPROVAL', 'RELEASED_TO_SHOP', 'IN_PRODUCTION', 'UNDER_QC']
    ).order_by('planned_end_date')[:10]

    # Today's active operations
    today_operations = JobRouteStep.objects.filter(
        status='IN_PROGRESS'
    ).select_related('route__job_card', 'operation', 'operator')[:10]

    # Recent job cards
    recent_jobs = JobCard.objects.order_by('-created_at')[:5]

    context = {
        'open_batches': open_batches,
        'open_job_cards': open_job_cards,
        'jobs_in_evaluation': jobs_in_evaluation,
        'jobs_awaiting_approval': jobs_awaiting_approval,
        'jobs_in_production': jobs_in_production,
        'urgent_jobs': urgent_jobs,
        'overdue_jobs': overdue_jobs,
        'today_operations': today_operations,
        'recent_jobs': recent_jobs,
    }
    return render(request, 'production/dashboard.html', context)


# ========== Batch Orders ==========

class BatchListView(LoginRequiredMixin, ListView):
    model = BatchOrder
    template_name = 'production/batches/list.html'
    context_object_name = 'batches'
    paginate_by = 25

    def get_queryset(self):
        qs = BatchOrder.objects.all()

        # Filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        customer = self.request.GET.get('customer')
        if customer:
            qs = qs.filter(customer_name__icontains=customer)

        bit_family = self.request.GET.get('bit_family')
        if bit_family:
            qs = qs.filter(bit_family=bit_family)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = BatchOrder.STATUS_CHOICES
        context['bit_family_choices'] = BatchOrder.BIT_FAMILY_CHOICES
        return context


class BatchDetailView(LoginRequiredMixin, DetailView):
    model = BatchOrder
    template_name = 'production/batches/detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_cards'] = self.object.job_cards.all().order_by('job_card_number')
        return context


class BatchCreateView(LoginRequiredMixin, CreateView):
    model = BatchOrder
    form_class = BatchOrderForm
    template_name = 'production/batches/form.html'

    def get_success_url(self):
        return reverse('production:batch_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Batch {form.instance.code} created successfully.")
        return super().form_valid(form)


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = BatchOrder
    form_class = BatchOrderForm
    template_name = 'production/batches/form.html'

    def get_success_url(self):
        return reverse('production:batch_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Batch {form.instance.code} updated successfully.")
        return super().form_valid(form)


# ========== Job Cards ==========

class JobCardListView(LoginRequiredMixin, ListView):
    model = JobCard
    template_name = 'production/jobcards/list.html'
    context_object_name = 'job_cards'
    paginate_by = 25

    def get_queryset(self):
        qs = JobCard.objects.select_related('serial_unit', 'batch_order')

        # Filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        job_type = self.request.GET.get('job_type')
        if job_type:
            qs = qs.filter(job_type=job_type)

        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        customer = self.request.GET.get('customer')
        if customer:
            qs = qs.filter(customer_name__icontains=customer)

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(job_card_number__icontains=search) |
                Q(serial_unit__serial_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(well_name__icontains=search)
            )

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = JobCard.STATUS_CHOICES
        context['job_type_choices'] = JobCard.JOB_TYPE_CHOICES
        context['priority_choices'] = JobCard.PRIORITY_CHOICES
        return context


class JobCardDetailView(LoginRequiredMixin, DetailView):
    model = JobCard
    template_name = 'production/jobcards/detail.html'
    context_object_name = 'job_card'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get or create route
        route, created = JobRoute.objects.get_or_create(job_card=self.object)
        context['route'] = route
        context['route_steps'] = route.steps.all().select_related('operation', 'operator')

        # Evaluations
        context['evaluations'] = self.object.cutter_evaluations.all()

        # Inspections
        context['thread_inspections'] = self.object.thread_inspections.all()
        context['ndt_reports'] = self.object.ndt_reports.all()

        # Checklists
        context['checklists'] = self.object.checklists.all()

        return context


class JobCardCreateView(LoginRequiredMixin, CreateView):
    model = JobCard
    form_class = JobCardForm
    template_name = 'production/jobcards/form.html'

    def get_success_url(self):
        return reverse('production:jobcard_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Create route for job card
        JobRoute.objects.create(job_card=self.object)

        # Auto-create checklists
        for template in ChecklistTemplate.objects.filter(auto_create_on_job=True, is_active=True):
            JobChecklistInstance.create_from_template(self.object, template)

        messages.success(self.request, f"Job Card {form.instance.job_card_number} created successfully.")
        return response


class JobCardUpdateView(LoginRequiredMixin, UpdateView):
    model = JobCard
    form_class = JobCardForm
    template_name = 'production/jobcards/form.html'

    def get_success_url(self):
        return reverse('production:jobcard_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Job Card {form.instance.job_card_number} updated successfully.")
        return super().form_valid(form)


# ========== Job Card Actions ==========

@login_required
def jobcard_start_evaluation(request, pk):
    """Start evaluation for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    job_card.start_evaluation(request.user)
    messages.success(request, f"Evaluation started for {job_card.job_card_number}.")
    return redirect('production:jobcard_detail', pk=pk)


@login_required
def jobcard_complete_evaluation(request, pk):
    """Complete evaluation for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    job_card.complete_evaluation(request.user)
    messages.success(request, f"Evaluation completed for {job_card.job_card_number}.")
    return redirect('production:jobcard_detail', pk=pk)


@login_required
def jobcard_release(request, pk):
    """Release job card to shop floor."""
    job_card = get_object_or_404(JobCard, pk=pk)
    job_card.release_to_shop(request.user)
    messages.success(request, f"Job Card {job_card.job_card_number} released to shop floor.")
    return redirect('production:jobcard_detail', pk=pk)


@login_required
def jobcard_start_production(request, pk):
    """Start production on job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    job_card.start_production()
    messages.success(request, f"Production started for {job_card.job_card_number}.")
    return redirect('production:jobcard_detail', pk=pk)


@login_required
def jobcard_complete(request, pk):
    """Complete job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    job_card.complete_job(request.user)
    messages.success(request, f"Job Card {job_card.job_card_number} completed.")
    return redirect('production:jobcard_detail', pk=pk)


# ========== Routing ==========

@login_required
def route_editor(request, pk):
    """Route editor for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    route, created = JobRoute.objects.get_or_create(job_card=job_card)
    steps = route.steps.all().select_related('operation', 'operator')

    # Available operations for adding
    operations = OperationDefinition.objects.filter(is_active=True).order_by('default_sequence')

    context = {
        'job_card': job_card,
        'route': route,
        'steps': steps,
        'operations': operations,
    }
    return render(request, 'production/routing/editor.html', context)


@login_required
def route_add_step(request, pk):
    """Add a step to the route."""
    job_card = get_object_or_404(JobCard, pk=pk)
    route, created = JobRoute.objects.get_or_create(job_card=job_card)

    if request.method == 'POST':
        form = RouteStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.route = route
            step.created_by = request.user
            step.save()
            messages.success(request, f"Step {step.operation.name} added to route.")
            return redirect('production:route_editor', pk=pk)
    else:
        # Default sequence: next multiple of 10
        last_step = route.steps.order_by('-sequence').first()
        next_seq = ((last_step.sequence // 10) + 1) * 10 if last_step else 10
        form = RouteStepForm(initial={'sequence': next_seq})

    context = {
        'job_card': job_card,
        'route': route,
        'form': form,
    }
    return render(request, 'production/routing/add_step.html', context)


@login_required
def route_step_start(request, step_pk):
    """Start a route step."""
    step = get_object_or_404(JobRouteStep, pk=step_pk)
    from floor_app.operations.hr.models import HREmployee

    # Try to get employee for current user
    operator = None
    try:
        if hasattr(request.user, 'hr_employee'):
            operator = request.user.hr_employee
    except:
        pass

    step.start_step(operator=operator)
    messages.success(request, f"Step {step.operation.name} started.")
    return redirect('production:route_editor', pk=step.route.job_card.pk)


@login_required
def route_step_complete(request, step_pk):
    """Complete a route step."""
    step = get_object_or_404(JobRouteStep, pk=step_pk)

    if request.method == 'POST':
        form = RouteStepCompleteForm(request.POST)
        if form.is_valid():
            step.complete_step(
                operator=form.cleaned_data.get('operator'),
                result_notes=form.cleaned_data.get('result_notes', '')
            )
            messages.success(request, f"Step {step.operation.name} completed.")
            return redirect('production:route_editor', pk=step.route.job_card.pk)
    else:
        form = RouteStepCompleteForm()

    context = {
        'step': step,
        'form': form,
    }
    return render(request, 'production/routing/complete_step.html', context)


@login_required
def route_step_skip(request, step_pk):
    """Skip a route step."""
    step = get_object_or_404(JobRouteStep, pk=step_pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        step.skip_step(reason=reason)
        messages.success(request, f"Step {step.operation.name} skipped.")

    return redirect('production:route_editor', pk=step.route.job_card.pk)


# ========== Cutter Evaluation ==========

@login_required
def evaluation_list(request, pk):
    """List all evaluations for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    evaluations = job_card.cutter_evaluations.all()

    context = {
        'job_card': job_card,
        'evaluations': evaluations,
    }
    return render(request, 'production/evaluation/list.html', context)


@login_required
def evaluation_create(request, pk):
    """Create a new cutter evaluation."""
    job_card = get_object_or_404(JobCard, pk=pk)

    if request.method == 'POST':
        form = CutterEvaluationHeaderForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.job_card = job_card

            # Set revision number
            existing_count = job_card.cutter_evaluations.filter(
                evaluation_type=evaluation.evaluation_type
            ).count()
            evaluation.revision_number = existing_count + 1

            # Set evaluator
            try:
                if hasattr(request.user, 'hr_employee'):
                    evaluation.evaluated_by = request.user.hr_employee
            except:
                pass

            evaluation.evaluated_at = timezone.now()
            evaluation.created_by = request.user
            evaluation.save()

            messages.success(request, "Evaluation created. Now enter cutter symbols.")
            return redirect('production:evaluation_edit', eval_pk=evaluation.pk)
    else:
        form = CutterEvaluationHeaderForm()

    context = {
        'job_card': job_card,
        'form': form,
    }
    return render(request, 'production/evaluation/create.html', context)


@login_required
def evaluation_detail(request, eval_pk):
    """View evaluation details."""
    evaluation = get_object_or_404(JobCutterEvaluationHeader, pk=eval_pk)
    details = evaluation.details.all().select_related('symbol')

    # Build grid from details
    grid_data = {}
    for detail in details:
        key = (detail.row, detail.column)
        grid_data[key] = detail

    context = {
        'evaluation': evaluation,
        'job_card': evaluation.job_card,
        'details': details,
        'grid_data': grid_data,
    }
    return render(request, 'production/evaluation/detail.html', context)


@login_required
def evaluation_edit(request, eval_pk):
    """Edit cutter evaluation grid."""
    evaluation = get_object_or_404(JobCutterEvaluationHeader, pk=eval_pk)
    symbols = CutterSymbol.objects.filter(is_active=True).order_by('sort_order')

    if request.method == 'POST':
        # Process grid data from POST
        # Format: cell_R_C = symbol_id
        for key, value in request.POST.items():
            if key.startswith('cell_') and value:
                parts = key.split('_')
                if len(parts) == 3:
                    row = int(parts[1])
                    col = int(parts[2])
                    symbol_id = int(value)

                    # Update or create detail
                    detail, created = JobCutterEvaluationDetail.objects.update_or_create(
                        header=evaluation,
                        row=row,
                        column=col,
                        defaults={
                            'symbol_id': symbol_id,
                            'created_by': request.user if created else evaluation.created_by,
                            'updated_by': request.user,
                        }
                    )

        # Recalculate summary
        evaluation.calculate_summary()
        messages.success(request, "Evaluation grid saved.")
        return redirect('production:evaluation_detail', eval_pk=eval_pk)

    # Build current grid state
    details = evaluation.details.all()
    grid_data = {}
    for detail in details:
        key = f"{detail.row}_{detail.column}"
        grid_data[key] = detail.symbol_id

    # Determine grid size (default 10x20)
    max_rows = 10
    max_cols = 20
    if evaluation.layout:
        max_rows = evaluation.layout.total_rows
        max_cols = evaluation.layout.total_columns

    context = {
        'evaluation': evaluation,
        'job_card': evaluation.job_card,
        'symbols': symbols,
        'grid_data': grid_data,
        'max_rows': max_rows,
        'max_cols': max_cols,
        'range_rows': range(1, max_rows + 1),
        'range_cols': range(1, max_cols + 1),
    }
    return render(request, 'production/evaluation/edit.html', context)


@login_required
def evaluation_submit(request, eval_pk):
    """Submit evaluation for review."""
    evaluation = get_object_or_404(JobCutterEvaluationHeader, pk=eval_pk)
    evaluation.submit_evaluation()
    messages.success(request, "Evaluation submitted for review.")
    return redirect('production:evaluation_detail', eval_pk=eval_pk)


@login_required
def evaluation_approve(request, eval_pk):
    """Approve evaluation."""
    evaluation = get_object_or_404(JobCutterEvaluationHeader, pk=eval_pk)
    evaluation.approve_evaluation(request.user)
    messages.success(request, "Evaluation approved.")
    return redirect('production:evaluation_detail', eval_pk=eval_pk)


# ========== NDT & Thread Inspection ==========

@login_required
def ndt_list(request, pk):
    """List NDT reports for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    reports = job_card.ndt_reports.all()

    context = {
        'job_card': job_card,
        'ndt_reports': reports,
    }
    return render(request, 'production/ndt/list.html', context)


class NdtCreateView(LoginRequiredMixin, CreateView):
    model = NdtReport
    form_class = NdtReportForm
    template_name = 'production/ndt/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.job_card = get_object_or_404(JobCard, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_card'] = self.job_card
        return context

    def form_valid(self, form):
        form.instance.job_card = self.job_card
        form.instance.created_by = self.request.user
        try:
            if hasattr(self.request.user, 'hr_employee'):
                form.instance.performed_by = self.request.user.hr_employee
        except:
            pass
        messages.success(self.request, "NDT report created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('production:ndt_detail', kwargs={'ndt_pk': self.object.pk})


class NdtUpdateView(LoginRequiredMixin, UpdateView):
    model = NdtReport
    form_class = NdtReportForm
    template_name = 'production/ndt/form.html'
    pk_url_kwarg = 'ndt_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_card'] = self.object.job_card
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "NDT report updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('production:ndt_detail', kwargs={'ndt_pk': self.object.pk})


@login_required
def ndt_detail(request, ndt_pk):
    """View NDT report details."""
    report = get_object_or_404(NdtReport, pk=ndt_pk)

    context = {
        'ndt_report': report,
        'job_card': report.job_card,
    }
    return render(request, 'production/ndt/detail.html', context)


@login_required
def thread_inspection_list(request, pk):
    """List thread inspections for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    inspections = job_card.thread_inspections.all()

    context = {
        'job_card': job_card,
        'thread_inspections': inspections,
    }
    return render(request, 'production/thread_inspection/list.html', context)


class ThreadInspectionCreateView(LoginRequiredMixin, CreateView):
    model = ApiThreadInspection
    form_class = ApiThreadInspectionForm
    template_name = 'production/thread_inspection/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.job_card = get_object_or_404(JobCard, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_card'] = self.job_card
        return context

    def form_valid(self, form):
        form.instance.job_card = self.job_card
        form.instance.created_by = self.request.user
        try:
            if hasattr(self.request.user, 'hr_employee'):
                form.instance.inspected_by = self.request.user.hr_employee
        except:
            pass
        messages.success(self.request, "Thread inspection created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('production:thread_inspection_detail', kwargs={'insp_pk': self.object.pk})


class ThreadInspectionUpdateView(LoginRequiredMixin, UpdateView):
    model = ApiThreadInspection
    form_class = ApiThreadInspectionForm
    template_name = 'production/thread_inspection/form.html'
    pk_url_kwarg = 'insp_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_card'] = self.object.job_card
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Thread inspection updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('production:thread_inspection_detail', kwargs={'insp_pk': self.object.pk})


@login_required
def thread_inspection_detail(request, insp_pk):
    """View thread inspection details."""
    inspection = get_object_or_404(ApiThreadInspection, pk=insp_pk)

    context = {
        'inspection': inspection,
        'job_card': inspection.job_card,
    }
    return render(request, 'production/thread_inspection/detail.html', context)


@login_required
def thread_inspection_complete_repair(request, insp_pk):
    """Complete repair on thread inspection."""
    inspection = get_object_or_404(ApiThreadInspection, pk=insp_pk)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        employee = None
        try:
            if hasattr(request.user, 'hr_employee'):
                employee = request.user.hr_employee
        except:
            pass

        inspection.complete_repair(employee, notes)
        messages.success(request, "Repair completed.")

    return redirect('production:thread_inspection_detail', insp_pk=insp_pk)


# ========== Checklists ==========

@login_required
def checklist_list(request, pk):
    """List checklists for a job card."""
    job_card = get_object_or_404(JobCard, pk=pk)
    checklists = job_card.checklists.all()

    context = {
        'job_card': job_card,
        'checklists': checklists,
    }
    return render(request, 'production/checklists/list.html', context)


@login_required
def checklist_detail(request, checklist_pk):
    """View checklist details."""
    checklist = get_object_or_404(JobChecklistInstance, pk=checklist_pk)
    items = checklist.items.all().select_related('checked_by')

    context = {
        'checklist': checklist,
        'job_card': checklist.job_card,
        'items': items,
    }
    return render(request, 'production/checklists/detail.html', context)


@login_required
def checklist_item_complete(request, item_pk):
    """Complete a checklist item."""
    item = get_object_or_404(JobChecklistItem, pk=item_pk)

    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        employee = None
        try:
            if hasattr(request.user, 'hr_employee'):
                employee = request.user.hr_employee
        except:
            pass

        item.mark_done(employee, comment)
        messages.success(request, f"Item marked as done.")

    return redirect('production:checklist_detail', checklist_pk=item.checklist.pk)


# ========== Settings ==========

@login_required
def settings_dashboard(request):
    """Settings dashboard for production module."""
    context = {
        'operation_count': OperationDefinition.objects.filter(is_active=True).count(),
        'symbol_count': CutterSymbol.objects.filter(is_active=True).count(),
        'template_count': ChecklistTemplate.objects.filter(is_active=True).count(),
    }
    return render(request, 'production/settings/dashboard.html', context)


class OperationListView(LoginRequiredMixin, ListView):
    model = OperationDefinition
    template_name = 'production/settings/operation_list.html'
    context_object_name = 'operations'

    def get_queryset(self):
        return OperationDefinition.objects.filter(is_active=True).order_by('sort_order', 'default_sequence')


class SymbolListView(LoginRequiredMixin, ListView):
    model = CutterSymbol
    template_name = 'production/settings/symbol_list.html'
    context_object_name = 'symbols'

    def get_queryset(self):
        return CutterSymbol.objects.filter(is_active=True).order_by('sort_order')


class ChecklistTemplateListView(LoginRequiredMixin, ListView):
    model = ChecklistTemplate
    template_name = 'production/settings/checklist_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return ChecklistTemplate.objects.filter(is_active=True).order_by('sort_order')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import (
    EvaluationSession,
    EvaluationCell,
    ThreadInspection,
    NDTInspection,
    TechnicalInstructionInstance,
    RequirementInstance,
    TechnicalInstructionTemplate,
    RequirementTemplate,
    CutterEvaluationCode,
    FeatureCode,
    BitSection,
    BitType,
    EvaluationSessionHistory,
)
from .forms import (
    EvaluationSessionForm,
    EvaluationCellForm,
    ThreadInspectionForm,
    NDTInspectionForm,
    TechnicalInstructionInstanceForm,
    RequirementInstanceForm,
    SessionReviewForm,
    SessionFilterForm,
)


# ========== Dashboard ==========

@login_required
def dashboard(request):
    """Evaluation dashboard with summary statistics."""

    # Summary stats
    total_sessions = EvaluationSession.objects.count()
    draft_sessions = EvaluationSession.objects.filter(status='DRAFT').count()
    pending_review = EvaluationSession.objects.filter(status='PENDING_REVIEW').count()
    approved_sessions = EvaluationSession.objects.filter(status='APPROVED').count()
    locked_sessions = EvaluationSession.objects.filter(is_locked=True).count()

    # Recent sessions
    recent_sessions = EvaluationSession.objects.select_related(
        'job_card', 'bit_type', 'evaluated_by'
    ).order_by('-created_at')[:10]

    # Sessions requiring attention
    attention_sessions = EvaluationSession.objects.filter(
        status__in=['PENDING_REVIEW', 'IN_PROGRESS']
    ).select_related('job_card', 'evaluated_by').order_by('-updated_at')[:10]

    # Statistics by status
    status_stats = EvaluationSession.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    context = {
        'total_sessions': total_sessions,
        'draft_sessions': draft_sessions,
        'pending_review': pending_review,
        'approved_sessions': approved_sessions,
        'locked_sessions': locked_sessions,
        'recent_sessions': recent_sessions,
        'attention_sessions': attention_sessions,
        'status_stats': status_stats,
    }
    return render(request, 'evaluation/dashboard.html', context)


# ========== Evaluation Session CRUD ==========

class EvaluationSessionListView(LoginRequiredMixin, ListView):
    model = EvaluationSession
    template_name = 'evaluation/sessions/list.html'
    context_object_name = 'sessions'
    paginate_by = 25

    def get_queryset(self):
        qs = EvaluationSession.objects.select_related(
            'job_card', 'bit_type', 'evaluated_by'
        )

        # Apply filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        bit_type = self.request.GET.get('bit_type')
        if bit_type:
            qs = qs.filter(bit_type_id=bit_type)

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(session_number__icontains=search) |
                Q(job_card__job_card_number__icontains=search) |
                Q(evaluation_notes__icontains=search)
            )

        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = SessionFilterForm(self.request.GET)
        context['status_choices'] = EvaluationSession.STATUS_CHOICES
        context['bit_types'] = BitType.objects.filter(is_active=True)
        return context


class EvaluationSessionDetailView(LoginRequiredMixin, DetailView):
    model = EvaluationSession
    template_name = 'evaluation/sessions/detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object

        # Get related data
        context['cells'] = session.cells.all().select_related(
            'evaluation_code', 'feature_code', 'section'
        )
        context['thread_inspections'] = session.thread_inspections.all()
        context['ndt_inspections'] = session.ndt_inspections.all()
        context['instructions'] = session.instruction_instances.all()
        context['requirements'] = session.requirement_instances.all()
        context['history'] = session.history.all().order_by('-performed_at')[:20]

        # Build grid data for visualization
        grid_data = {}
        for cell in context['cells']:
            key = f"{cell.row}_{cell.column}"
            grid_data[key] = {
                'pocket_number': cell.pocket_number,
                'code': cell.evaluation_code.code if cell.evaluation_code else '',
                'color': cell.evaluation_code.color if cell.evaluation_code else '#ffffff',
            }
        context['grid_data'] = grid_data

        return context


class EvaluationSessionCreateView(LoginRequiredMixin, CreateView):
    model = EvaluationSession
    form_class = EvaluationSessionForm
    template_name = 'evaluation/sessions/form.html'

    def get_success_url(self):
        return reverse('evaluation:session_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        # Set evaluator if user has HR employee profile
        try:
            if hasattr(self.request.user, 'hr_employee'):
                form.instance.evaluated_by = self.request.user.hr_employee
        except:
            pass

        response = super().form_valid(form)

        # Auto-apply technical instructions and requirements
        self._apply_templates(self.object)

        # Log creation
        EvaluationSessionHistory.objects.create(
            session=self.object,
            action='CREATED',
            description=f"Session {self.object.session_number} created",
            performed_by=self.request.user
        )

        messages.success(self.request, f"Evaluation session {form.instance.session_number} created successfully.")
        return response

    def _apply_templates(self, session):
        """Apply auto-apply instruction and requirement templates."""
        # Apply technical instruction templates
        instruction_templates = TechnicalInstructionTemplate.objects.filter(
            auto_apply=True, is_active=True
        )
        if session.bit_type:
            instruction_templates = instruction_templates.filter(
                Q(applies_to_bit_type__isnull=True) | Q(applies_to_bit_type=session.bit_type)
            )

        for template in instruction_templates:
            TechnicalInstructionInstance.objects.create(
                session=session,
                template=template,
                code=template.code,
                title=template.title,
                description=template.description,
                is_mandatory=template.is_mandatory,
            )

        # Apply requirement templates
        requirement_templates = RequirementTemplate.objects.filter(
            auto_apply=True, is_active=True
        )
        if session.bit_type:
            requirement_templates = requirement_templates.filter(
                Q(applies_to_bit_type__isnull=True) | Q(applies_to_bit_type=session.bit_type)
            )

        for template in requirement_templates:
            RequirementInstance.objects.create(
                session=session,
                template=template,
                code=template.code,
                title=template.title,
                description=template.description,
                category=template.category,
                is_mandatory=template.is_mandatory,
                verification_method=template.verification_method,
            )


class EvaluationSessionUpdateView(LoginRequiredMixin, UpdateView):
    model = EvaluationSession
    form_class = EvaluationSessionForm
    template_name = 'evaluation/sessions/form.html'

    def get_success_url(self):
        return reverse('evaluation:session_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Evaluation session {form.instance.session_number} updated successfully.")
        return super().form_valid(form)


# ========== Grid Editor ==========

@login_required
def grid_editor(request, pk):
    """Interactive cutter/pocket map editor."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        messages.warning(request, "This session is locked and cannot be edited.")
        return redirect('evaluation:session_detail', pk=pk)

    # Get available codes
    evaluation_codes = CutterEvaluationCode.objects.filter(is_active=True).order_by('sort_order')
    feature_codes = FeatureCode.objects.filter(is_active=True).order_by('sort_order')
    sections = BitSection.objects.filter(is_active=True).order_by('sort_order')

    # Build current grid state
    cells = session.cells.all()
    grid_data = {}
    for cell in cells:
        key = f"{cell.row}_{cell.column}"
        grid_data[key] = {
            'id': cell.id,
            'pocket_number': cell.pocket_number,
            'evaluation_code_id': cell.evaluation_code_id,
            'feature_code_id': cell.feature_code_id,
            'section_id': cell.section_id,
            'condition_description': cell.condition_description,
            'notes': cell.notes,
            'wear_percentage': float(cell.wear_percentage) if cell.wear_percentage else None,
        }

    context = {
        'session': session,
        'evaluation_codes': evaluation_codes,
        'feature_codes': feature_codes,
        'sections': sections,
        'grid_data': json.dumps(grid_data),
        'max_rows': session.total_rows,
        'max_cols': session.total_columns,
        'range_rows': range(1, session.total_rows + 1),
        'range_cols': range(1, session.total_columns + 1),
    }
    return render(request, 'evaluation/sessions/grid_editor.html', context)


@login_required
@require_POST
def save_cell(request, pk):
    """AJAX endpoint for saving cell updates."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        return JsonResponse({'success': False, 'error': 'Session is locked'}, status=403)

    try:
        data = json.loads(request.body)
        row = data.get('row')
        column = data.get('column')

        # Update or create cell
        cell, created = EvaluationCell.objects.update_or_create(
            session=session,
            row=row,
            column=column,
            defaults={
                'pocket_number': data.get('pocket_number', row * session.total_columns + column),
                'evaluation_code_id': data.get('evaluation_code_id') or None,
                'feature_code_id': data.get('feature_code_id') or None,
                'section_id': data.get('section_id') or None,
                'condition_description': data.get('condition_description', ''),
                'notes': data.get('notes', ''),
                'wear_percentage': data.get('wear_percentage') or None,
                'evaluated_at': timezone.now(),
            }
        )

        # Recalculate summary
        session.calculate_summary()

        # Log the change
        EvaluationSessionHistory.objects.create(
            session=session,
            action='CELL_UPDATED',
            description=f"Cell ({row},{column}) updated",
            new_value=json.dumps(data),
            performed_by=request.user
        )

        return JsonResponse({
            'success': True,
            'cell_id': cell.id,
            'created': created,
            'summary': {
                'total_cutters': session.total_cutters,
                'replace_count': session.replace_count,
                'repair_count': session.repair_count,
                'ok_count': session.ok_count,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ========== Thread Inspection ==========

@login_required
def thread_inspection(request, pk):
    """View/manage thread inspections for a session."""
    session = get_object_or_404(EvaluationSession, pk=pk)
    inspections = session.thread_inspections.all()

    context = {
        'session': session,
        'inspections': inspections,
        'form': ThreadInspectionForm(),
    }
    return render(request, 'evaluation/sessions/thread_inspection.html', context)


@login_required
@require_POST
def save_thread_inspection(request, pk):
    """Save thread inspection."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        messages.error(request, "Session is locked and cannot be modified.")
        return redirect('evaluation:thread_inspection', pk=pk)

    form = ThreadInspectionForm(request.POST)
    if form.is_valid():
        inspection = form.save(commit=False)
        inspection.session = session
        inspection.created_by = request.user
        inspection.updated_by = request.user

        try:
            if hasattr(request.user, 'hr_employee'):
                inspection.inspected_by = request.user.hr_employee
        except:
            pass

        inspection.save()
        messages.success(request, "Thread inspection saved successfully.")
    else:
        messages.error(request, "Error saving thread inspection. Please check the form.")

    return redirect('evaluation:thread_inspection', pk=pk)


# ========== NDT Inspection ==========

@login_required
def ndt_inspection(request, pk):
    """View/manage NDT inspections for a session."""
    session = get_object_or_404(EvaluationSession, pk=pk)
    inspections = session.ndt_inspections.all()

    context = {
        'session': session,
        'inspections': inspections,
        'form': NDTInspectionForm(),
    }
    return render(request, 'evaluation/sessions/ndt_inspection.html', context)


@login_required
@require_POST
def save_ndt_inspection(request, pk):
    """Save NDT inspection."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        messages.error(request, "Session is locked and cannot be modified.")
        return redirect('evaluation:ndt_inspection', pk=pk)

    form = NDTInspectionForm(request.POST)
    if form.is_valid():
        inspection = form.save(commit=False)
        inspection.session = session
        inspection.created_by = request.user
        inspection.updated_by = request.user

        try:
            if hasattr(request.user, 'hr_employee'):
                inspection.performed_by = request.user.hr_employee
        except:
            pass

        inspection.save()
        messages.success(request, "NDT inspection saved successfully.")
    else:
        messages.error(request, "Error saving NDT inspection. Please check the form.")

    return redirect('evaluation:ndt_inspection', pk=pk)


# ========== Technical Instructions ==========

@login_required
def instructions_list(request, pk):
    """List technical instructions for a session."""
    session = get_object_or_404(EvaluationSession, pk=pk)
    instructions = session.instruction_instances.all().select_related('template')

    context = {
        'session': session,
        'instructions': instructions,
    }
    return render(request, 'evaluation/sessions/instructions.html', context)


@login_required
@require_POST
def accept_instruction(request, inst_pk):
    """Accept a technical instruction."""
    instruction = get_object_or_404(TechnicalInstructionInstance, pk=inst_pk)

    if instruction.session.is_locked:
        messages.error(request, "Session is locked.")
        return redirect('evaluation:instructions_list', pk=instruction.session.pk)

    notes = request.POST.get('notes', '')

    try:
        employee = request.user.hr_employee if hasattr(request.user, 'hr_employee') else None
    except:
        employee = None

    instruction.accept(employee, notes)

    # Log the action
    EvaluationSessionHistory.objects.create(
        session=instruction.session,
        action='INSTRUCTION_ACTIONED',
        description=f"Instruction {instruction.code} accepted",
        performed_by=request.user
    )

    messages.success(request, f"Instruction {instruction.code} accepted.")
    return redirect('evaluation:instructions_list', pk=instruction.session.pk)


@login_required
@require_POST
def reject_instruction(request, inst_pk):
    """Reject a technical instruction."""
    instruction = get_object_or_404(TechnicalInstructionInstance, pk=inst_pk)

    if instruction.session.is_locked:
        messages.error(request, "Session is locked.")
        return redirect('evaluation:instructions_list', pk=instruction.session.pk)

    notes = request.POST.get('notes', '')

    try:
        employee = request.user.hr_employee if hasattr(request.user, 'hr_employee') else None
    except:
        employee = None

    instruction.reject(employee, notes)

    # Log the action
    EvaluationSessionHistory.objects.create(
        session=instruction.session,
        action='INSTRUCTION_ACTIONED',
        description=f"Instruction {instruction.code} rejected",
        performed_by=request.user
    )

    messages.success(request, f"Instruction {instruction.code} rejected.")
    return redirect('evaluation:instructions_list', pk=instruction.session.pk)


# ========== Requirements ==========

@login_required
def requirements_list(request, pk):
    """List requirements for a session."""
    session = get_object_or_404(EvaluationSession, pk=pk)
    requirements = session.requirement_instances.all().select_related('template')

    context = {
        'session': session,
        'requirements': requirements,
    }
    return render(request, 'evaluation/sessions/requirements.html', context)


@login_required
@require_POST
def satisfy_requirement(request, req_pk):
    """Mark a requirement as satisfied."""
    requirement = get_object_or_404(RequirementInstance, pk=req_pk)

    if requirement.session.is_locked:
        messages.error(request, "Session is locked.")
        return redirect('evaluation:requirements_list', pk=requirement.session.pk)

    notes = request.POST.get('notes', '')
    verification_result = request.POST.get('verification_result', '')

    try:
        employee = request.user.hr_employee if hasattr(request.user, 'hr_employee') else None
    except:
        employee = None

    requirement.satisfy(employee, notes, verification_result)

    # Log the action
    EvaluationSessionHistory.objects.create(
        session=requirement.session,
        action='REQUIREMENT_SATISFIED',
        description=f"Requirement {requirement.code} satisfied",
        performed_by=request.user
    )

    messages.success(request, f"Requirement {requirement.code} marked as satisfied.")
    return redirect('evaluation:requirements_list', pk=requirement.session.pk)


# ========== Engineer Review & Approval ==========

@login_required
def engineer_review(request, pk):
    """Engineer review page for evaluation session."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    # Check all requirements and instructions
    pending_instructions = session.instruction_instances.filter(status='PENDING').count()
    unsatisfied_requirements = session.requirement_instances.filter(status='NOT_SATISFIED').count()
    mandatory_unsatisfied = session.requirement_instances.filter(
        status='NOT_SATISFIED', is_mandatory=True
    ).count()

    context = {
        'session': session,
        'pending_instructions': pending_instructions,
        'unsatisfied_requirements': unsatisfied_requirements,
        'mandatory_unsatisfied': mandatory_unsatisfied,
        'form': SessionReviewForm(),
        'cells': session.cells.all().select_related('evaluation_code'),
        'thread_inspections': session.thread_inspections.all(),
        'ndt_inspections': session.ndt_inspections.all(),
    }
    return render(request, 'evaluation/sessions/engineer_review.html', context)


@login_required
@require_POST
def approve_session(request, pk):
    """Approve the evaluation session."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        messages.error(request, "Session is already locked.")
        return redirect('evaluation:session_detail', pk=pk)

    notes = request.POST.get('notes', '')

    session.approve(request.user, notes)

    # Log the approval
    EvaluationSessionHistory.objects.create(
        session=session,
        action='APPROVED',
        description=f"Session approved by {request.user.username}",
        new_value=notes,
        performed_by=request.user
    )

    messages.success(request, f"Session {session.session_number} approved successfully.")
    return redirect('evaluation:session_detail', pk=pk)


@login_required
@require_POST
def lock_session(request, pk):
    """Lock the evaluation session to prevent further edits."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    if session.is_locked:
        messages.warning(request, "Session is already locked.")
        return redirect('evaluation:session_detail', pk=pk)

    session.lock_session(request.user)

    # Log the lock
    EvaluationSessionHistory.objects.create(
        session=session,
        action='LOCKED',
        description=f"Session locked by {request.user.username}",
        performed_by=request.user
    )

    messages.success(request, f"Session {session.session_number} has been locked.")
    return redirect('evaluation:session_detail', pk=pk)


# ========== Print Views ==========

@login_required
def print_job_card(request, pk):
    """Print-friendly job card view."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    # Build complete grid data
    grid_data = {}
    for cell in session.cells.all().select_related('evaluation_code'):
        key = f"{cell.row}_{cell.column}"
        grid_data[key] = cell

    context = {
        'session': session,
        'grid_data': grid_data,
        'cells': session.cells.all(),
        'thread_inspections': session.thread_inspections.all(),
        'ndt_inspections': session.ndt_inspections.all(),
        'instructions': session.instruction_instances.all(),
        'requirements': session.requirement_instances.all(),
        'range_rows': range(1, session.total_rows + 1),
        'range_cols': range(1, session.total_columns + 1),
    }
    return render(request, 'evaluation/sessions/print_job_card.html', context)


@login_required
def print_summary(request, pk):
    """Print summary report."""
    session = get_object_or_404(EvaluationSession, pk=pk)

    context = {
        'session': session,
        'history': session.history.all().order_by('performed_at'),
    }
    return render(request, 'evaluation/sessions/print_summary.html', context)


# ========== History ==========

@login_required
def history_view(request, pk):
    """View evaluation session history."""
    session = get_object_or_404(EvaluationSession, pk=pk)
    history = session.history.all().order_by('-performed_at')

    context = {
        'session': session,
        'history': history,
    }
    return render(request, 'evaluation/sessions/history.html', context)


# ========== Settings Views ==========

@login_required
def settings_dashboard(request):
    """Settings dashboard for evaluation module."""
    context = {
        'code_count': CutterEvaluationCode.objects.filter(is_active=True).count(),
        'feature_count': FeatureCode.objects.filter(is_active=True).count(),
        'section_count': BitSection.objects.filter(is_active=True).count(),
        'type_count': BitType.objects.filter(is_active=True).count(),
        'instruction_template_count': TechnicalInstructionTemplate.objects.filter(is_active=True).count(),
        'requirement_template_count': RequirementTemplate.objects.filter(is_active=True).count(),
    }
    return render(request, 'evaluation/settings/dashboard.html', context)


class CodeListView(LoginRequiredMixin, ListView):
    model = CutterEvaluationCode
    template_name = 'evaluation/settings/code_list.html'
    context_object_name = 'codes'

    def get_queryset(self):
        return CutterEvaluationCode.objects.filter(is_active=True).order_by('sort_order')


class FeatureListView(LoginRequiredMixin, ListView):
    model = FeatureCode
    template_name = 'evaluation/settings/feature_list.html'
    context_object_name = 'features'

    def get_queryset(self):
        return FeatureCode.objects.filter(is_active=True).order_by('sort_order')


class SectionListView(LoginRequiredMixin, ListView):
    model = BitSection
    template_name = 'evaluation/settings/section_list.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return BitSection.objects.filter(is_active=True).order_by('sort_order')


class TypeListView(LoginRequiredMixin, ListView):
    model = BitType
    template_name = 'evaluation/settings/type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return BitType.objects.filter(is_active=True).order_by('sort_order')


class InstructionTemplateListView(LoginRequiredMixin, ListView):
    model = TechnicalInstructionTemplate
    template_name = 'evaluation/settings/instruction_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return TechnicalInstructionTemplate.objects.filter(is_active=True).order_by('-priority', 'code')


class RequirementTemplateListView(LoginRequiredMixin, ListView):
    model = RequirementTemplate
    template_name = 'evaluation/settings/requirement_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return RequirementTemplate.objects.filter(is_active=True).order_by('category', 'code')

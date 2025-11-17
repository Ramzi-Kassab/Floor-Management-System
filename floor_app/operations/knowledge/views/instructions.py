"""
Instruction Rule Engine views.
This is the POWERFUL interface for managing dynamic instructions.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.db.models import Q
from django.utils import timezone

from ..models import InstructionRule, RuleCondition, RuleAction, InstructionExecutionLog
from ..services import RuleEngine
from ..forms import InstructionRuleForm


class InstructionListView(LoginRequiredMixin, ListView):
    """List all instruction rules."""
    model = InstructionRule
    template_name = 'knowledge/instruction_list.html'
    context_object_name = 'instructions'
    paginate_by = 15

    def get_queryset(self):
        qs = InstructionRule.objects.filter(
            is_deleted=False
        ).select_related('owner_department').prefetch_related('conditions', 'actions')

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)

        # Filter by type
        instruction_type = self.request.GET.get('type', '')
        if instruction_type:
            qs = qs.filter(instruction_type=instruction_type)

        # Filter by priority
        priority = self.request.GET.get('priority', '')
        if priority:
            qs = qs.filter(priority=priority)

        # Filter by default/temporary
        scope = self.request.GET.get('scope', '')
        if scope == 'default':
            qs = qs.filter(is_default=True)
        elif scope == 'temporary':
            qs = qs.filter(is_temporary=True)

        # Search
        query = self.request.GET.get('q', '')
        if query:
            qs = qs.filter(
                Q(code__icontains=query) |
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        return qs.order_by('execution_order', '-priority')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['instruction_types'] = InstructionRule.InstructionType.choices
        context['priorities'] = InstructionRule.Priority.choices
        context['statuses'] = InstructionRule.Status.choices
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'status': self.request.GET.get('status', ''),
            'type': self.request.GET.get('type', ''),
            'priority': self.request.GET.get('priority', ''),
            'scope': self.request.GET.get('scope', ''),
        }
        return context


class InstructionCreateView(PermissionRequiredMixin, CreateView):
    """Create new instruction rule."""
    model = InstructionRule
    form_class = InstructionRuleForm
    template_name = 'knowledge/instruction_form.html'
    permission_required = 'knowledge.add_instructionrule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Available models for conditions
        context['available_models'] = self._get_available_models()
        context['operators'] = RuleCondition.Operator.choices
        context['action_types'] = RuleAction.ActionType.choices
        return context

    def _get_available_models(self):
        """Get models that can be used in conditions."""
        models = []
        # HR models
        for model_name in ['HREmployee', 'HRPeople', 'Department', 'Position']:
            try:
                ct = ContentType.objects.get(app_label='hr', model=model_name.lower())
                models.append({'id': ct.id, 'name': f'HR: {model_name}'})
            except ContentType.DoesNotExist:
                pass

        # Future: Add Inventory, Production models here
        return models

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = InstructionRule.Status.DRAFT
        messages.success(self.request, 'Instruction rule created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('knowledge:instruction_detail', kwargs={'code': self.object.code})


class InstructionUpdateView(PermissionRequiredMixin, UpdateView):
    """Edit existing instruction rule."""
    model = InstructionRule
    form_class = InstructionRuleForm
    template_name = 'knowledge/instruction_form.html'
    permission_required = 'knowledge.change_instructionrule'

    def get_queryset(self):
        return InstructionRule.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instruction = self.object
        context['conditions'] = instruction.conditions.all().order_by('condition_group', 'order')
        context['actions'] = instruction.actions.all().order_by('order')
        context['scopes'] = instruction.target_scopes.all()
        context['operators'] = RuleCondition.Operator.choices
        context['action_types'] = RuleAction.ActionType.choices
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Instruction rule updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('knowledge:instruction_detail', kwargs={'code': self.object.code})


@login_required
def instruction_detail(request, code):
    """View instruction rule details."""
    instruction = get_object_or_404(
        InstructionRule.objects.select_related('owner_department', 'source_article')
        .prefetch_related('conditions', 'actions', 'target_scopes', 'attachments'),
        code=code,
        is_deleted=False
    )

    # Get recent execution logs
    recent_logs = InstructionExecutionLog.objects.filter(
        instruction=instruction
    ).order_by('-executed_at')[:20]

    context = {
        'instruction': instruction,
        'conditions': instruction.conditions.all().order_by('condition_group', 'order'),
        'actions': instruction.actions.all().order_by('order'),
        'scopes': instruction.target_scopes.all(),
        'recent_logs': recent_logs,
    }

    return render(request, 'knowledge/instruction_detail.html', context)


@login_required
@permission_required('knowledge.can_activate_instruction')
def instruction_activate(request, pk):
    """Activate or deactivate an instruction."""
    instruction = get_object_or_404(InstructionRule, pk=pk, is_deleted=False)

    if instruction.status == InstructionRule.Status.ACTIVE:
        instruction.status = InstructionRule.Status.INACTIVE
        messages.info(request, f'Instruction "{instruction.code}" has been deactivated.')
    elif instruction.status in [InstructionRule.Status.APPROVED, InstructionRule.Status.INACTIVE]:
        instruction.status = InstructionRule.Status.ACTIVE
        messages.success(request, f'Instruction "{instruction.code}" has been activated.')
    else:
        messages.warning(request, 'Instruction must be approved before activation.')
        return redirect('knowledge:instruction_detail', code=instruction.code)

    instruction.save()
    return redirect('knowledge:instruction_detail', code=instruction.code)


@login_required
def get_available_models(request):
    """API: Get all models that can be used in instruction conditions."""
    models = []

    # Get all ContentTypes
    app_labels = ['hr', 'knowledge', 'auth']  # Add more as modules are created

    for ct in ContentType.objects.filter(app_label__in=app_labels):
        model_class = ct.model_class()
        if model_class:
            models.append({
                'id': ct.id,
                'app_label': ct.app_label,
                'model': ct.model,
                'name': f"{ct.app_label}.{ct.model}",
                'verbose_name': model_class._meta.verbose_name
            })

    return JsonResponse({'models': models})


@login_required
def get_model_fields(request, ct_id):
    """API: Get all fields of a model for condition building."""
    try:
        ct = ContentType.objects.get(id=ct_id)
        model_class = ct.model_class()
    except ContentType.DoesNotExist:
        return JsonResponse({'error': 'Model not found'}, status=404)

    fields = []
    for field in model_class._meta.get_fields():
        # Skip reverse relations and private fields
        if field.auto_created and not field.concrete:
            continue
        if field.name.startswith('_'):
            continue

        field_info = {
            'name': field.name,
            'verbose_name': getattr(field, 'verbose_name', field.name),
            'type': field.__class__.__name__,
            'is_relation': field.is_relation,
        }

        # Add choices if available
        if hasattr(field, 'choices') and field.choices:
            field_info['choices'] = list(field.choices)

        # For relations, indicate related model
        if field.is_relation and hasattr(field, 'related_model'):
            related_ct = ContentType.objects.get_for_model(field.related_model)
            field_info['related_model'] = {
                'id': related_ct.id,
                'name': f"{related_ct.app_label}.{related_ct.model}"
            }

        fields.append(field_info)

    return JsonResponse({
        'model': f"{ct.app_label}.{ct.model}",
        'fields': fields
    })


@login_required
def evaluate_instruction_preview(request):
    """API: Preview instruction evaluation (for testing)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    instruction_id = data.get('instruction_id')
    context_data = data.get('context', {})

    if not instruction_id:
        return JsonResponse({'error': 'instruction_id required'}, status=400)

    try:
        instruction = InstructionRule.objects.get(pk=instruction_id)
    except InstructionRule.DoesNotExist:
        return JsonResponse({'error': 'Instruction not found'}, status=404)

    # Build context from provided data
    context = {}
    for ct_id_str, obj_id in context_data.items():
        ct_id = int(ct_id_str)
        try:
            ct = ContentType.objects.get(id=ct_id)
            model_class = ct.model_class()
            obj = model_class.objects.get(pk=obj_id)
            context[ct_id] = obj
        except Exception as e:
            return JsonResponse({'error': f'Error loading {ct_id}: {str(e)}'}, status=400)

    # Evaluate
    engine = RuleEngine(user=request.user, request=request)

    # Don't log preview evaluations
    from ..services.rule_engine import RuleEvaluator
    evaluator = RuleEvaluator(instruction)
    result, details = evaluator.evaluate(context)

    return JsonResponse({
        'instruction': instruction.code,
        'result': result,
        'evaluation_details': details
    })


@login_required
def applicable_instructions_api(request, model, object_id):
    """API: Get instructions applicable to a specific object."""
    try:
        ct = ContentType.objects.get(model=model.lower())
    except ContentType.DoesNotExist:
        return JsonResponse({'error': 'Model not found'}, status=404)

    engine = RuleEngine(user=request.user, request=request)
    instructions = engine.get_applicable_instructions(ct, object_id)

    result = []
    for inst in instructions:
        result.append({
            'id': inst.pk,
            'code': inst.code,
            'title': inst.title,
            'type': inst.get_instruction_type_display(),
            'priority': inst.priority,
            'is_default': inst.is_default,
            'is_temporary': inst.is_temporary,
            'description': inst.short_description or inst.description[:200]
        })

    return JsonResponse({'instructions': result})

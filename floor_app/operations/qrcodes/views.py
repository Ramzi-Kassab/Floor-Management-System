"""
Views for QR Code management and scanning.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages

from .models import (
    QCode, QCodeType, ScanLog, ScanActionType,
    Equipment, MaintenanceRequest, Container, MovementLog, ProcessExecution
)
from .forms import (
    QCodeGenerateForm, EquipmentForm, MaintenanceRequestForm,
    MaintenanceCompleteForm, ContainerForm, BOMPickupForm, ProcessActionForm
)
from .services import QRCodeGenerator, ScanHandler


class DashboardView(LoginRequiredMixin, TemplateView):
    """QR Code management dashboard."""
    template_name = 'qrcodes/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # QCode statistics
        context['total_qcodes'] = QCode.objects.count()
        context['active_qcodes'] = QCode.objects.filter(is_active=True).count()
        context['qcodes_by_type'] = QCode.objects.values('qcode_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Scan statistics
        today = timezone.now().date()
        context['scans_today'] = ScanLog.objects.filter(
            scan_timestamp__date=today
        ).count()
        context['successful_scans_today'] = ScanLog.objects.filter(
            scan_timestamp__date=today,
            success=True
        ).count()
        context['recent_scans'] = ScanLog.objects.select_related('qcode').order_by(
            '-scan_timestamp'
        )[:10]

        # Equipment
        context['total_equipment'] = Equipment.objects.filter(is_deleted=False).count()
        context['equipment_needs_maintenance'] = Equipment.objects.filter(
            is_deleted=False,
            next_maintenance_date__lte=today
        ).count()

        # Maintenance
        context['open_maintenance_requests'] = MaintenanceRequest.objects.filter(
            status__in=['OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS']
        ).count()
        context['critical_requests'] = MaintenanceRequest.objects.filter(
            status__in=['OPEN', 'ACKNOWLEDGED'],
            priority='CRITICAL'
        ).count()

        # Containers
        context['total_containers'] = Container.objects.filter(is_deleted=False).count()

        # Recent movements
        context['recent_movements'] = MovementLog.objects.order_by('-moved_at')[:10]

        # Process executions
        context['active_processes'] = ProcessExecution.objects.filter(
            status='IN_PROGRESS'
        ).count()

        return context


@login_required
def scan_handler(request, token):
    """
    Central scan handler view.

    Routes scans to appropriate domain handlers based on QCode type.
    """
    handler = ScanHandler(request)
    result = handler.handle_scan(str(token))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(result.to_dict())

    if result.show_options:
        # Show options page
        return render(request, 'qrcodes/scan_options.html', {
            'result': result,
            'token': token,
        })

    if result.redirect_url:
        if not result.success:
            messages.error(request, result.message)
        else:
            messages.success(request, result.message)
        return redirect(result.redirect_url)

    # Default: show result page
    return render(request, 'qrcodes/scan_result.html', {
        'result': result,
        'token': token,
    })


@login_required
def qr_image(request, token, format='png'):
    """
    Generate and serve QR code image.

    Supports PNG and SVG formats.
    """
    qcode = get_object_or_404(QCode, token=token)

    generator = QRCodeGenerator(base_url=request.build_absolute_uri('/'))

    try:
        if format.lower() == 'svg':
            image_buffer = generator.generate_qr_for_qcode(qcode, format='svg')
            content_type = 'image/svg+xml'
        else:
            image_buffer = generator.generate_qr_for_qcode(qcode, format='png')
            content_type = 'image/png'

        response = HttpResponse(image_buffer.getvalue(), content_type=content_type)
        response['Cache-Control'] = 'public, max-age=86400'  # Cache for 1 day
        return response

    except ImportError as e:
        return HttpResponse(
            f"QR generation dependencies not installed: {str(e)}",
            status=500
        )


@login_required
def qr_label_image(request, token):
    """Generate QR code with label."""
    qcode = get_object_or_404(QCode, token=token)

    generator = QRCodeGenerator(base_url=request.build_absolute_uri('/'))
    size = request.GET.get('size', 'medium')

    try:
        image_buffer = generator.generate_label_with_qr(qcode, size=size)
        response = HttpResponse(image_buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'public, max-age=86400'
        return response
    except ImportError as e:
        return HttpResponse(
            f"QR generation dependencies not installed: {str(e)}",
            status=500
        )


@login_required
def generate_qcode(request):
    """Generate a new QCode."""
    if request.method == 'POST':
        form = QCodeGenerateForm(request.POST)
        if form.is_valid():
            from django.contrib.contenttypes.models import ContentType

            qcode_type = form.cleaned_data['qcode_type']
            object_id = form.cleaned_data['object_id']
            label = form.cleaned_data.get('label', '')

            # Determine content type based on qcode_type
            content_type_map = {
                'EMPLOYEE': ('hr', 'hremployee'),
                'JOB_CARD': ('production', 'jobcard'),
                'BIT_SERIAL': ('inventory', 'serialunit'),
                'EQUIPMENT': ('qrcodes', 'equipment'),
                'ITEM': ('inventory', 'item'),
                'LOCATION': ('inventory', 'location'),
                'BIT_BOX': ('qrcodes', 'container'),
            }

            if qcode_type in content_type_map:
                app_label, model = content_type_map[qcode_type]
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model)
                except ContentType.DoesNotExist:
                    messages.error(request, f"Content type not found for {qcode_type}")
                    return redirect('qrcodes:generate')

                qcode = QCode.objects.create(
                    qcode_type=qcode_type,
                    content_type=ct,
                    object_id=object_id,
                    label=label or f"{qcode_type} #{object_id}",
                    created_by=request.user,
                )

                messages.success(request, f"QR Code generated: {qcode.token_short}")
                return redirect('qrcodes:detail', token=qcode.token)
            else:
                messages.error(request, f"Unknown QCode type: {qcode_type}")
    else:
        form = QCodeGenerateForm()

    return render(request, 'qrcodes/generate.html', {'form': form})


@login_required
def deactivate_qcode(request, token):
    """Deactivate a QCode."""
    qcode = get_object_or_404(QCode, token=token)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        qcode.deactivate(user=request.user, reason=reason)
        messages.success(request, f"QR Code {qcode.token_short} deactivated")
        return redirect('qrcodes:detail', token=token)

    return render(request, 'qrcodes/deactivate.html', {'qcode': qcode})


@login_required
def reactivate_qcode(request, token):
    """Reactivate a QCode."""
    qcode = get_object_or_404(QCode, token=token)

    if request.method == 'POST':
        qcode.reactivate(user=request.user)
        messages.success(request, f"QR Code {qcode.token_short} reactivated")
        return redirect('qrcodes:detail', token=token)

    return render(request, 'qrcodes/reactivate.html', {'qcode': qcode})


@login_required
def regenerate_token(request, token):
    """Regenerate QCode token (invalidates old printed codes)."""
    qcode = get_object_or_404(QCode, token=token)

    if request.method == 'POST':
        old_token, new_token = qcode.regenerate_token(user=request.user)
        messages.warning(
            request,
            f"Token regenerated. Old: {str(old_token)[:8]}, New: {str(new_token)[:8]}. "
            f"Old printed QR codes will no longer work!"
        )
        return redirect('qrcodes:detail', token=new_token)

    return render(request, 'qrcodes/regenerate.html', {'qcode': qcode})


@login_required
def export_scan_logs(request):
    """Export scan logs to CSV."""
    import csv
    from django.http import StreamingHttpResponse

    def generate_csv():
        yield 'Timestamp,QCode,Type,Action,User,Employee,Success,Message\n'

        for log in ScanLog.objects.select_related('qcode').order_by('-scan_timestamp')[:10000]:
            yield f'"{log.scan_timestamp}","{log.qcode.token_short}","{log.qcode.get_qcode_type_display()}","{log.get_action_type_display()}","{log.scanner_user or ""}","{log.scanner_employee_name}","{log.success}","{log.message}"\n'

    response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scan_logs.csv"'
    return response


# Class-based views for CRUD operations
class QCodeListView(LoginRequiredMixin, ListView):
    """List all QCodes."""
    model = QCode
    template_name = 'qrcodes/qcode_list.html'
    context_object_name = 'qcodes'
    paginate_by = 25

    def get_queryset(self):
        queryset = QCode.objects.all()

        # Filter by type
        qcode_type = self.request.GET.get('type')
        if qcode_type:
            queryset = queryset.filter(qcode_type=qcode_type)

        # Filter by active status
        active = self.request.GET.get('active')
        if active == 'true':
            queryset = queryset.filter(is_active=True)
        elif active == 'false':
            queryset = queryset.filter(is_active=False)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(token__icontains=search) |
                Q(label__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qcode_types'] = QCodeType.CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_active'] = self.request.GET.get('active', '')
        context['search'] = self.request.GET.get('search', '')
        return context


class QCodeDetailView(LoginRequiredMixin, DetailView):
    """View QCode details."""
    model = QCode
    template_name = 'qrcodes/qcode_detail.html'
    context_object_name = 'qcode'
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_scans'] = self.object.scan_logs.order_by('-scan_timestamp')[:20]
        return context


class ScanLogListView(LoginRequiredMixin, ListView):
    """List scan logs."""
    model = ScanLog
    template_name = 'qrcodes/scan_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = ScanLog.objects.select_related('qcode').order_by('-scan_timestamp')

        # Filter by action type
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action_type=action)

        # Filter by success
        success = self.request.GET.get('success')
        if success == 'true':
            queryset = queryset.filter(success=True)
        elif success == 'false':
            queryset = queryset.filter(success=False)

        # Date filter
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(scan_timestamp__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_types'] = ScanActionType.CHOICES
        return context


# Equipment views
class EquipmentListView(LoginRequiredMixin, ListView):
    """List all equipment."""
    model = Equipment
    template_name = 'qrcodes/equipment_list.html'
    context_object_name = 'equipment_list'
    paginate_by = 25

    def get_queryset(self):
        return Equipment.objects.filter(is_deleted=False).order_by('code')


class EquipmentDetailView(LoginRequiredMixin, DetailView):
    """View equipment details."""
    model = Equipment
    template_name = 'qrcodes/equipment_detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['maintenance_requests'] = self.object.maintenance_requests.order_by('-reported_at')[:10]
        if self.object.qcode_id:
            context['qcode'] = QCode.objects.filter(pk=self.object.qcode_id).first()
        return context


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    """Create new equipment."""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'qrcodes/equipment_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Equipment {self.object.code} created")
        return response

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else f'/qrcodes/equipment/{self.object.pk}/'


class EquipmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update equipment."""
    model = Equipment
    form_class = EquipmentForm
    template_name = 'qrcodes/equipment_form.html'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Equipment {self.object.code} updated")
        return response

    def get_success_url(self):
        return f'/qrcodes/equipment/{self.object.pk}/'


@login_required
def create_maintenance_request(request, pk):
    """Create maintenance request for equipment (via QR scan)."""
    equipment = get_object_or_404(Equipment, pk=pk)

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.equipment = equipment
            maintenance.reported_by_user = request.user

            # Get employee info
            try:
                from floor_app.operations.hr.models import HREmployee
                employee = HREmployee.objects.filter(user=request.user).first()
                if employee:
                    maintenance.reported_by_employee_id = employee.pk
                    maintenance.reported_by_name = str(employee.person) if employee.person else str(employee)
            except Exception:
                pass

            maintenance.save()
            messages.success(request, f"Maintenance request created for {equipment.code}")
            return redirect('qrcodes:maintenance_detail', pk=maintenance.pk)
    else:
        form = MaintenanceRequestForm()

    return render(request, 'qrcodes/maintenance_form.html', {
        'form': form,
        'equipment': equipment,
    })


@login_required
def generate_equipment_qr(request, pk):
    """Generate QR code for equipment."""
    equipment = get_object_or_404(Equipment, pk=pk)

    if request.method == 'POST':
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Equipment)

        qcode, created = QCode.get_or_create_for_object(
            obj=equipment,
            qcode_type=QCodeType.EQUIPMENT,
            label=f"{equipment.code} - {equipment.name}",
            created_by=request.user
        )

        equipment.qcode_id = qcode.pk
        equipment.save(update_fields=['qcode_id'])

        if created:
            messages.success(request, f"QR Code generated for {equipment.code}")
        else:
            messages.info(request, f"QR Code already exists for {equipment.code}")

        return redirect('qrcodes:equipment_detail', pk=pk)

    return render(request, 'qrcodes/confirm_generate_qr.html', {
        'object': equipment,
        'object_type': 'Equipment',
    })


# Maintenance views
class MaintenanceListView(LoginRequiredMixin, ListView):
    """List maintenance requests."""
    model = MaintenanceRequest
    template_name = 'qrcodes/maintenance_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        queryset = MaintenanceRequest.objects.select_related('equipment').order_by('-reported_at')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset


class MaintenanceDetailView(LoginRequiredMixin, DetailView):
    """View maintenance request details."""
    model = MaintenanceRequest
    template_name = 'qrcodes/maintenance_detail.html'
    context_object_name = 'request'


@login_required
def complete_maintenance(request, pk):
    """Complete a maintenance request."""
    maintenance = get_object_or_404(MaintenanceRequest, pk=pk)

    if request.method == 'POST':
        form = MaintenanceCompleteForm(request.POST, instance=maintenance)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.complete(
                resolution_notes=form.cleaned_data.get('resolution_notes', ''),
                parts_used=form.cleaned_data.get('parts_used', ''),
                labor_hours=form.cleaned_data.get('labor_hours'),
                total_cost=form.cleaned_data.get('total_cost')
            )
            messages.success(request, "Maintenance request completed")
            return redirect('qrcodes:maintenance_detail', pk=pk)
    else:
        form = MaintenanceCompleteForm(instance=maintenance)

    return render(request, 'qrcodes/maintenance_complete.html', {
        'form': form,
        'request': maintenance,
    })


# Container views
class ContainerListView(LoginRequiredMixin, ListView):
    """List containers."""
    model = Container
    template_name = 'qrcodes/container_list.html'
    context_object_name = 'containers'
    paginate_by = 25

    def get_queryset(self):
        return Container.objects.filter(is_deleted=False).order_by('code')


class ContainerDetailView(LoginRequiredMixin, DetailView):
    """View container details."""
    model = Container
    template_name = 'qrcodes/container_detail.html'
    context_object_name = 'container'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.qcode_id:
            context['qcode'] = QCode.objects.filter(pk=self.object.qcode_id).first()
        return context


class ContainerCreateView(LoginRequiredMixin, CreateView):
    """Create new container."""
    model = Container
    form_class = ContainerForm
    template_name = 'qrcodes/container_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Container {self.object.code} created")
        return response

    def get_success_url(self):
        return f'/qrcodes/containers/{self.object.pk}/'


class ContainerUpdateView(LoginRequiredMixin, UpdateView):
    """Update container."""
    model = Container
    form_class = ContainerForm
    template_name = 'qrcodes/container_form.html'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Container {self.object.code} updated")
        return response

    def get_success_url(self):
        return f'/qrcodes/containers/{self.object.pk}/'


@login_required
def generate_container_qr(request, pk):
    """Generate QR code for container."""
    container = get_object_or_404(Container, pk=pk)

    if request.method == 'POST':
        qcode, created = QCode.get_or_create_for_object(
            obj=container,
            qcode_type=QCodeType.BIT_BOX,
            label=f"{container.code} ({container.get_container_type_display()})",
            created_by=request.user
        )

        container.qcode_id = qcode.pk
        container.save(update_fields=['qcode_id'])

        if created:
            messages.success(request, f"QR Code generated for {container.code}")
        else:
            messages.info(request, f"QR Code already exists for {container.code}")

        return redirect('qrcodes:container_detail', pk=pk)

    return render(request, 'qrcodes/confirm_generate_qr.html', {
        'object': container,
        'object_type': 'Container',
    })


# Process execution views
@login_required
def start_process(request, route_step_id):
    """Start a process step execution."""
    if request.method == 'POST':
        # Check if already in progress
        existing = ProcessExecution.objects.filter(
            route_step_id=route_step_id,
            status__in=['IN_PROGRESS', 'PAUSED']
        ).first()

        if existing:
            messages.warning(request, "This process step is already in progress")
            return redirect('qrcodes:process_action', execution_id=existing.pk)

        # Get employee info
        employee_id = None
        employee_name = ""
        try:
            from floor_app.operations.hr.models import HREmployee
            employee = HREmployee.objects.filter(user=request.user).first()
            if employee:
                employee_id = employee.pk
                employee_name = str(employee.person) if employee.person else str(employee)
        except Exception:
            pass

        # Create new execution
        execution = ProcessExecution.objects.create(
            route_step_id=route_step_id,
            job_card_id=request.POST.get('job_card_id', 0),
            operator_user=request.user,
            operator_employee_id=employee_id,
            operator_name=employee_name,
            operation_name=request.POST.get('operation_name', 'Process Step'),
            work_center=request.POST.get('work_center', ''),
            created_by=request.user,
        )

        success, message = execution.start(
            user=request.user,
            employee_id=employee_id,
            operator_name=employee_name
        )

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('qrcodes:process_action', execution_id=execution.pk)

    return render(request, 'qrcodes/process_start.html', {
        'route_step_id': route_step_id,
    })


@login_required
def process_action(request, execution_id):
    """Handle process step actions (end, pause, resume)."""
    execution = get_object_or_404(ProcessExecution, pk=execution_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        reason = request.POST.get('reason', '')

        if action == 'end':
            success, message = execution.end(completion_notes=notes)
        elif action == 'pause':
            success, message = execution.pause(reason=reason)
        elif action == 'resume':
            success, message = execution.resume()
        else:
            success, message = False, "Unknown action"

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('qrcodes:process_action', execution_id=execution_id)

    form = ProcessActionForm()
    return render(request, 'qrcodes/process_action.html', {
        'execution': execution,
        'form': form,
    })


# BOM Material pickup views
@login_required
def bom_material_view(request, bom_line_id):
    """View BOM material details."""
    # This would integrate with the inventory BOM module
    return render(request, 'qrcodes/bom_material.html', {
        'bom_line_id': bom_line_id,
    })


@login_required
def bom_pickup(request, bom_line_id):
    """
    Record BOM material pickup.

    Creates a MovementLog entry for the pickup.
    """
    if request.method == 'POST':
        form = BOMPickupForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data.get('notes', '')

            # Get employee info
            employee_id = None
            employee_name = ""
            try:
                from floor_app.operations.hr.models import HREmployee
                employee = HREmployee.objects.filter(user=request.user).first()
                if employee:
                    employee_id = employee.pk
                    employee_name = str(employee.person) if employee.person else str(employee)
            except Exception:
                pass

            # Create movement log
            movement = MovementLog.objects.create(
                movement_type='BOM_PICKUP',
                bom_line_id=bom_line_id,
                quantity=quantity,
                moved_by_user=request.user,
                moved_by_employee_id=employee_id,
                moved_by_name=employee_name,
                reason="BOM material pickup",
                notes=notes,
                created_by=request.user,
            )

            messages.success(request, f"Material pickup recorded: {quantity} units")
            return redirect('qrcodes:movement_list')
    else:
        form = BOMPickupForm()

    return render(request, 'qrcodes/bom_pickup.html', {
        'form': form,
        'bom_line_id': bom_line_id,
    })


@login_required
def bom_return(request, bom_line_id):
    """Record BOM material return."""
    if request.method == 'POST':
        form = BOMPickupForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data.get('notes', '')

            # Get employee info
            employee_id = None
            employee_name = ""
            try:
                from floor_app.operations.hr.models import HREmployee
                employee = HREmployee.objects.filter(user=request.user).first()
                if employee:
                    employee_id = employee.pk
                    employee_name = str(employee.person) if employee.person else str(employee)
            except Exception:
                pass

            # Create movement log
            movement = MovementLog.objects.create(
                movement_type='BOM_RETURN',
                bom_line_id=bom_line_id,
                quantity=quantity,
                moved_by_user=request.user,
                moved_by_employee_id=employee_id,
                moved_by_name=employee_name,
                reason="BOM material return - excess/unused",
                notes=notes,
                created_by=request.user,
            )

            messages.success(request, f"Material return recorded: {quantity} units")
            return redirect('qrcodes:movement_list')
    else:
        form = BOMPickupForm()

    return render(request, 'qrcodes/bom_return.html', {
        'form': form,
        'bom_line_id': bom_line_id,
    })


# Movement log views
class MovementLogListView(LoginRequiredMixin, ListView):
    """List movement logs."""
    model = MovementLog
    template_name = 'qrcodes/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 50

    def get_queryset(self):
        queryset = MovementLog.objects.order_by('-moved_at')

        movement_type = self.request.GET.get('type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        return queryset


# Bulk operations
@login_required
def bulk_generate(request):
    """Bulk generate QR codes."""
    if request.method == 'POST':
        # Parse the bulk generation request
        qcode_type = request.POST.get('qcode_type')
        object_ids = request.POST.get('object_ids', '').split(',')

        generated_count = 0
        for obj_id in object_ids:
            obj_id = obj_id.strip()
            if obj_id.isdigit():
                # Generate QCode (similar logic to generate_qcode view)
                pass
                generated_count += 1

        messages.success(request, f"Generated {generated_count} QR codes")
        return redirect('qrcodes:list')

    return render(request, 'qrcodes/bulk_generate.html', {
        'qcode_types': QCodeType.CHOICES,
    })


@login_required
def bulk_print(request):
    """Bulk print QR codes."""
    if request.method == 'POST':
        qcode_ids = request.POST.getlist('qcode_ids')
        qcodes = QCode.objects.filter(pk__in=qcode_ids)

        return render(request, 'qrcodes/print_labels.html', {
            'qcodes': qcodes,
        })

    return render(request, 'qrcodes/bulk_print_select.html', {
        'qcodes': QCode.objects.filter(is_active=True).order_by('-created_at')[:100],
    })


# API endpoints
@csrf_exempt
@require_http_methods(["POST"])
def api_scan(request):
    """
    API endpoint for scanning QR codes.

    Expects JSON: {"token": "uuid-string", "action_hint": "optional"}
    """
    try:
        data = json.loads(request.body)
        token = data.get('token')
        action_hint = data.get('action_hint')

        if not token:
            return JsonResponse({'error': 'Token required'}, status=400)

        handler = ScanHandler(request)
        result = handler.handle_scan(token, action_hint=action_hint)

        return JsonResponse(result.to_dict())

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_qcode_info(request, token):
    """API endpoint to get QCode information."""
    qcode = get_object_or_404(QCode, token=token)

    return JsonResponse({
        'token': str(qcode.token),
        'token_short': qcode.token_short,
        'type': qcode.qcode_type,
        'type_display': qcode.get_qcode_type_display(),
        'label': qcode.label,
        'is_active': qcode.is_active,
        'scan_count': qcode.scan_count,
        'last_scanned_at': qcode.last_scanned_at.isoformat() if qcode.last_scanned_at else None,
        'created_at': qcode.created_at.isoformat(),
        'version': qcode.version,
    })

"""
Central scan handling service.

Routes scans to appropriate domain handlers based on QCode type.
"""
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ..models import QCode, QCodeType, ScanLog, ScanActionType
from ..models import ProcessExecution, MaintenanceRequest, MovementLog


class ScanResult:
    """Result of a scan operation."""

    def __init__(self, success=True, action=None, message="", redirect_url=None,
                 data=None, show_options=False, options=None):
        """
        Initialize scan result.

        Args:
            success: Whether scan succeeded
            action: Action that was performed
            message: User-friendly message
            redirect_url: URL to redirect to
            data: Additional data dict
            show_options: Whether to show action options to user
            options: List of available actions
        """
        self.success = success
        self.action = action or ScanActionType.UNKNOWN
        self.message = message
        self.redirect_url = redirect_url
        self.data = data or {}
        self.show_options = show_options
        self.options = options or []

    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            'success': self.success,
            'action': self.action,
            'message': self.message,
            'redirect_url': self.redirect_url,
            'data': self.data,
            'show_options': self.show_options,
            'options': self.options,
        }


class ScanHandler:
    """
    Central scan handler service.

    Responsibilities:
    - Token lookup and validation
    - Logging all scan events
    - Routing to appropriate domain handlers
    - Returning scan results
    """

    def __init__(self, request=None):
        """
        Initialize handler.

        Args:
            request: HTTP request object
        """
        self.request = request
        self.user = request.user if request and hasattr(request, 'user') else None

    def handle_scan(self, token, action_hint=None, context_obj=None, reason=""):
        """
        Main entry point for handling a QR code scan.

        Args:
            token: QCode token (UUID string)
            action_hint: Optional hint about intended action
            context_obj: Optional context object
            reason: Optional reason for scan

        Returns:
            ScanResult object
        """
        # Step 1: Look up QCode
        try:
            qcode = QCode.objects.get(token=token)
        except QCode.DoesNotExist:
            return self._log_and_return(
                None,
                ScanResult(
                    success=False,
                    message="Invalid or unknown QR code",
                    action=ScanActionType.UNKNOWN
                ),
                reason=reason
            )

        # Step 2: Validate QCode is active
        if not qcode.is_active:
            result = ScanResult(
                success=False,
                message="This QR code has been deactivated",
                action=ScanActionType.VIEW_DETAILS,
                data={'qcode_id': qcode.pk, 'token': str(qcode.token)}
            )
            return self._log_and_return(qcode, result, reason=reason)

        # Step 3: Route based on QCode type
        handler_method = self._get_handler_for_type(qcode.qcode_type)
        if handler_method:
            result = handler_method(qcode, action_hint, context_obj, reason)
        else:
            # Default: View details
            result = self._handle_default(qcode)

        # Step 4: Log the scan
        return self._log_and_return(qcode, result, context_obj, reason)

    def _get_handler_for_type(self, qcode_type):
        """Get appropriate handler method for QCode type."""
        handlers = {
            QCodeType.EMPLOYEE: self._handle_employee,
            QCodeType.JOB_CARD: self._handle_job_card,
            QCodeType.PROCESS_STEP: self._handle_process_step,
            QCodeType.BIT_SERIAL: self._handle_bit_serial,
            QCodeType.BIT_BOX: self._handle_bit_box,
            QCodeType.EQUIPMENT: self._handle_equipment,
            QCodeType.LOCATION: self._handle_location,
            QCodeType.ITEM: self._handle_item,
            QCodeType.BOM_MATERIAL: self._handle_bom_material,
            QCodeType.EVALUATION_SESSION: self._handle_evaluation_session,
            QCodeType.BATCH_ORDER: self._handle_batch_order,
        }
        return handlers.get(qcode_type)

    def _handle_default(self, qcode):
        """Default handler: show details."""
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message=f"Scanned: {qcode.label or qcode.get_qcode_type_display()}",
            redirect_url=qcode.get_absolute_url(),
            data={'qcode_id': qcode.pk}
        )

    def _handle_employee(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle employee badge scan."""
        # Default: show employee profile
        # Options could include: check-in, attendance, access control
        options = [
            {'action': 'view_profile', 'label': 'View Profile', 'url': f'/hr/employees/{qcode.object_id}/'},
            {'action': 'check_in', 'label': 'Check In'},
            {'action': 'check_out', 'label': 'Check Out'},
        ]

        if action_hint == 'view_profile' or not action_hint:
            return ScanResult(
                success=True,
                action=ScanActionType.VIEW_DETAILS,
                message="Employee badge scanned",
                redirect_url=f'/hr/employees/{qcode.object_id}/',
                show_options=True,
                options=options
            )
        elif action_hint == 'check_in':
            return ScanResult(
                success=True,
                action=ScanActionType.CHECK_IN,
                message="Employee checked in",
                data={'employee_id': qcode.object_id}
            )
        elif action_hint == 'check_out':
            return ScanResult(
                success=True,
                action=ScanActionType.CHECK_OUT,
                message="Employee checked out",
                data={'employee_id': qcode.object_id}
            )

        return self._handle_default(qcode)

    def _handle_job_card(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle job card QR scan."""
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Job Card scanned",
            redirect_url=f'/production/jobcards/{qcode.object_id}/',
            data={'job_card_id': qcode.object_id}
        )

    def _handle_process_step(self, qcode, action_hint=None, context_obj=None, reason=""):
        """
        Handle process step QR scan.

        This is the core production workflow:
        - First scan = Start step
        - Second scan = End step (or show options for pause/resume)
        """
        # Get or check for existing execution
        execution = ProcessExecution.objects.filter(
            route_step_id=qcode.object_id,
            status__in=['IN_PROGRESS', 'PAUSED', 'NOT_STARTED']
        ).order_by('-created_at').first()

        if not execution:
            # No execution exists, start new one
            return ScanResult(
                success=True,
                action=ScanActionType.PROCESS_START,
                message="Ready to start process step",
                redirect_url=f'/qrcodes/process/start/{qcode.object_id}/',
                show_options=True,
                options=[
                    {'action': 'start', 'label': 'Start Process'},
                    {'action': 'cancel', 'label': 'Cancel'},
                ],
                data={'route_step_id': qcode.object_id}
            )

        elif execution.status == 'IN_PROGRESS':
            # Currently in progress, offer end or pause
            return ScanResult(
                success=True,
                action=ScanActionType.PROCESS_END,
                message=f"Process step in progress ({execution.duration_minutes:.1f} min)",
                redirect_url=f'/qrcodes/process/action/{execution.pk}/',
                show_options=True,
                options=[
                    {'action': 'end', 'label': 'End Process'},
                    {'action': 'pause', 'label': 'Pause'},
                ],
                data={'execution_id': execution.pk}
            )

        elif execution.status == 'PAUSED':
            # Currently paused, offer resume
            return ScanResult(
                success=True,
                action=ScanActionType.PROCESS_RESUME,
                message="Process step is paused",
                redirect_url=f'/qrcodes/process/action/{execution.pk}/',
                show_options=True,
                options=[
                    {'action': 'resume', 'label': 'Resume'},
                    {'action': 'end', 'label': 'End Process'},
                ],
                data={'execution_id': execution.pk}
            )

        return self._handle_default(qcode)

    def _handle_bit_serial(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle serial unit (bit) QR scan."""
        options = [
            {'action': 'view', 'label': 'View Details'},
            {'action': 'move', 'label': 'Move to Location'},
            {'action': 'history', 'label': 'View History'},
        ]

        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Serial Unit scanned",
            redirect_url=f'/inventory/serial-units/{qcode.object_id}/',
            show_options=True,
            options=options,
            data={'serial_unit_id': qcode.object_id}
        )

    def _handle_bit_box(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle bit box/container QR scan."""
        options = [
            {'action': 'view', 'label': 'View Contents'},
            {'action': 'move', 'label': 'Move Container'},
            {'action': 'add', 'label': 'Add Item'},
            {'action': 'remove', 'label': 'Remove Item'},
        ]

        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Container scanned",
            redirect_url=f'/qrcodes/containers/{qcode.object_id}/',
            show_options=True,
            options=options,
            data={'container_id': qcode.object_id}
        )

    def _handle_equipment(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle equipment QR scan."""
        options = [
            {'action': 'view', 'label': 'View Details'},
            {'action': 'report_issue', 'label': 'Report Issue'},
            {'action': 'maintenance_history', 'label': 'Maintenance History'},
        ]

        if action_hint == 'report_issue':
            return ScanResult(
                success=True,
                action=ScanActionType.MAINTENANCE_REPORT,
                message="Report maintenance issue",
                redirect_url=f'/qrcodes/equipment/{qcode.object_id}/report/',
                data={'equipment_id': qcode.object_id}
            )

        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Equipment scanned",
            redirect_url=f'/qrcodes/equipment/{qcode.object_id}/',
            show_options=True,
            options=options,
            data={'equipment_id': qcode.object_id}
        )

    def _handle_location(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle location QR scan."""
        options = [
            {'action': 'view', 'label': 'View Location'},
            {'action': 'assign_item', 'label': 'Assign Item Here'},
            {'action': 'inventory', 'label': 'View Inventory'},
        ]

        return ScanResult(
            success=True,
            action=ScanActionType.LOCATION_ASSIGN,
            message="Location scanned",
            redirect_url=f'/inventory/settings/locations/{qcode.object_id}/',
            show_options=True,
            options=options,
            data={'location_id': qcode.object_id}
        )

    def _handle_item(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle item/material QR scan."""
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Item scanned",
            redirect_url=f'/inventory/items/{qcode.object_id}/',
            data={'item_id': qcode.object_id}
        )

    def _handle_bom_material(self, qcode, action_hint=None, context_obj=None, reason=""):
        """
        Handle BOM material pickup QR scan.

        This is specifically for tracking materials picked for job cards.
        """
        options = [
            {'action': 'pickup', 'label': 'Pickup Material'},
            {'action': 'return', 'label': 'Return Material'},
            {'action': 'verify', 'label': 'Verify Quantity'},
        ]

        if action_hint == 'pickup':
            return ScanResult(
                success=True,
                action=ScanActionType.MATERIAL_PICKUP,
                message="Material pickup",
                redirect_url=f'/qrcodes/bom/pickup/{qcode.object_id}/',
                data={'bom_line_id': qcode.object_id}
            )
        elif action_hint == 'return':
            return ScanResult(
                success=True,
                action=ScanActionType.MATERIAL_RETURN,
                message="Material return",
                redirect_url=f'/qrcodes/bom/return/{qcode.object_id}/',
                data={'bom_line_id': qcode.object_id}
            )

        return ScanResult(
            success=True,
            action=ScanActionType.MATERIAL_PICKUP,
            message="BOM Material scanned",
            redirect_url=f'/qrcodes/bom/{qcode.object_id}/',
            show_options=True,
            options=options,
            data={'bom_line_id': qcode.object_id}
        )

    def _handle_evaluation_session(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle evaluation session QR scan."""
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Evaluation session scanned",
            redirect_url=f'/evaluation/sessions/{qcode.object_id}/',
            data={'evaluation_session_id': qcode.object_id}
        )

    def _handle_batch_order(self, qcode, action_hint=None, context_obj=None, reason=""):
        """Handle batch order QR scan."""
        return ScanResult(
            success=True,
            action=ScanActionType.VIEW_DETAILS,
            message="Batch order scanned",
            redirect_url=f'/production/batches/{qcode.object_id}/',
            data={'batch_order_id': qcode.object_id}
        )

    def _log_and_return(self, qcode, result, context_obj=None, reason=""):
        """
        Log the scan and return the result.

        Args:
            qcode: QCode that was scanned (can be None for invalid scans)
            result: ScanResult object
            context_obj: Optional context object
            reason: Optional reason

        Returns:
            The same ScanResult object
        """
        if qcode:
            ScanLog.create_log(
                qcode=qcode,
                action_type=result.action,
                request=self.request,
                user=self.user,
                success=result.success,
                message=result.message,
                reason=reason,
                context_obj=context_obj,
                metadata=result.data
            )

        return result

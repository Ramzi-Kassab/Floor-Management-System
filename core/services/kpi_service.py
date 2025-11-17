"""
Central KPI Service

Aggregates KPIs from all modules for unified dashboard reporting.
"""

from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from datetime import timedelta


class KPIService:
    """
    Central service for calculating and aggregating KPIs across all modules.
    """

    @classmethod
    def get_all_kpis(cls):
        """Get all KPIs from all modules"""
        return {
            'hr': cls.get_hr_kpis(),
            'inventory': cls.get_inventory_kpis(),
            'production': cls.get_production_kpis(),
            'purchasing': cls.get_purchasing_kpis(),
            'evaluation': cls.get_evaluation_kpis(),
            'qrcodes': cls.get_qrcodes_kpis(),
        }

    @classmethod
    def get_hr_kpis(cls):
        """HR Module KPIs"""
        try:
            from floor_app.operations.hr.models import (
                HREmployee, LeaveRequest, AttendanceRecord
            )

            today = timezone.now().date()
            month_start = today.replace(day=1)

            total_employees = HREmployee.objects.filter(status='ACTIVE').count()
            on_leave_today = LeaveRequest.objects.filter(
                status='APPROVED',
                start_date__lte=today,
                end_date__gte=today
            ).count()

            # Attendance percentage this month
            total_attendance = AttendanceRecord.objects.filter(
                date__gte=month_start,
                date__lte=today
            ).count()
            present_count = AttendanceRecord.objects.filter(
                date__gte=month_start,
                date__lte=today,
                status__in=['PRESENT', 'LATE']
            ).count()

            attendance_rate = 0
            if total_attendance > 0:
                attendance_rate = (present_count / total_attendance) * 100

            return {
                'total_active_employees': total_employees,
                'on_leave_today': on_leave_today,
                'attendance_rate': round(attendance_rate, 2),
                'pending_leave_requests': LeaveRequest.objects.filter(
                    status='PENDING_APPROVAL'
                ).count(),
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_inventory_kpis(cls):
        """Inventory Module KPIs"""
        try:
            from floor_app.operations.inventory.models import (
                Item, InventoryStock, SerialUnit
            )

            total_items = Item.objects.count()
            total_stock_value = InventoryStock.objects.aggregate(
                total=Sum(F('qty_on_hand') * F('unit_cost'))
            )['total'] or 0

            low_stock_items = InventoryStock.objects.filter(
                qty_on_hand__lte=F('reorder_point')
            ).count()

            active_serial_units = SerialUnit.objects.filter(
                status__in=['AVAILABLE', 'IN_PRODUCTION']
            ).count()

            return {
                'total_items': total_items,
                'total_stock_value': float(total_stock_value),
                'low_stock_items': low_stock_items,
                'active_serial_units': active_serial_units,
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_production_kpis(cls):
        """Production Module KPIs"""
        try:
            from floor_app.operations.production.models import (
                BatchOrder, JobCard
            )

            today = timezone.now().date()

            active_batches = BatchOrder.objects.filter(
                status__in=['SCHEDULED', 'IN_PROGRESS']
            ).count()

            jobs_in_progress = JobCard.objects.filter(
                status='IN_PROGRESS'
            ).count()

            # On-time delivery rate
            completed_jobs = JobCard.objects.filter(
                status='COMPLETED'
            ).count()
            on_time_jobs = JobCard.objects.filter(
                status='COMPLETED',
                actual_end_date__lte=F('planned_end_date')
            ).count()

            on_time_rate = 0
            if completed_jobs > 0:
                on_time_rate = (on_time_jobs / completed_jobs) * 100

            return {
                'active_batches': active_batches,
                'jobs_in_progress': jobs_in_progress,
                'on_time_delivery_rate': round(on_time_rate, 2),
                'total_completed_jobs': completed_jobs,
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_purchasing_kpis(cls):
        """Purchasing Module KPIs"""
        try:
            from floor_app.operations.purchasing.models import (
                PurchaseOrder, SupplierInvoice, Supplier
            )

            open_pos = PurchaseOrder.objects.filter(
                status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED']
            ).count()

            total_po_value = PurchaseOrder.objects.filter(
                status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'FULLY_RECEIVED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            overdue_invoices = SupplierInvoice.objects.filter(
                payment_status='OVERDUE'
            ).count()

            total_payables = SupplierInvoice.objects.filter(
                payment_status__in=['NOT_PAID', 'PARTIAL', 'OVERDUE']
            ).aggregate(total=Sum('amount_outstanding'))['total'] or 0

            avg_supplier_rating = Supplier.objects.filter(
                status='ACTIVE'
            ).aggregate(avg=Avg('quality_rating'))['avg'] or 0

            return {
                'open_purchase_orders': open_pos,
                'total_po_value': float(total_po_value),
                'overdue_invoices': overdue_invoices,
                'total_payables': float(total_payables),
                'avg_supplier_rating': round(float(avg_supplier_rating), 2),
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_evaluation_kpis(cls):
        """Evaluation Module KPIs"""
        try:
            from floor_app.operations.evaluation.models import (
                EvaluationSession
            )

            total_evaluations = EvaluationSession.objects.count()
            pending_evaluations = EvaluationSession.objects.filter(
                status='PENDING'
            ).count()

            avg_score = EvaluationSession.objects.filter(
                status='COMPLETED'
            ).aggregate(avg=Avg('overall_score'))['avg'] or 0

            return {
                'total_evaluations': total_evaluations,
                'pending_evaluations': pending_evaluations,
                'average_score': round(float(avg_score), 2),
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_qrcodes_kpis(cls):
        """QR Codes Module KPIs"""
        try:
            from floor_app.operations.qrcodes.models import (
                QCode, Equipment, MaintenanceRequest
            )

            today = timezone.now().date()

            total_qrcodes = QCode.objects.filter(is_active=True).count()
            total_equipment = Equipment.objects.count()
            equipment_needing_maintenance = Equipment.objects.filter(
                next_maintenance_date__lte=today
            ).count()
            open_maintenance_requests = MaintenanceRequest.objects.filter(
                status__in=['REPORTED', 'ACKNOWLEDGED', 'IN_PROGRESS']
            ).count()

            return {
                'total_active_qrcodes': total_qrcodes,
                'total_equipment': total_equipment,
                'equipment_needing_maintenance': equipment_needing_maintenance,
                'open_maintenance_requests': open_maintenance_requests,
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_critical_alerts(cls):
        """Get critical alerts across all modules"""
        alerts = []

        # Inventory alerts
        try:
            from floor_app.operations.inventory.models import InventoryStock
            low_stock = InventoryStock.objects.filter(
                qty_on_hand__lte=F('reorder_point')
            ).count()
            if low_stock > 0:
                alerts.append({
                    'module': 'inventory',
                    'severity': 'warning',
                    'message': f'{low_stock} items below reorder point',
                    'count': low_stock
                })
        except Exception:
            pass

        # Purchasing alerts
        try:
            from floor_app.operations.purchasing.models import SupplierInvoice
            overdue = SupplierInvoice.objects.filter(payment_status='OVERDUE').count()
            if overdue > 0:
                alerts.append({
                    'module': 'purchasing',
                    'severity': 'danger',
                    'message': f'{overdue} overdue invoices',
                    'count': overdue
                })
        except Exception:
            pass

        # HR alerts - expiring documents
        try:
            from floor_app.operations.hr.models import EmployeeDocument
            today = timezone.now().date()
            expiring = EmployeeDocument.objects.filter(
                expiry_date__lte=today + timedelta(days=30),
                expiry_date__gt=today
            ).count()
            if expiring > 0:
                alerts.append({
                    'module': 'hr',
                    'severity': 'warning',
                    'message': f'{expiring} documents expiring within 30 days',
                    'count': expiring
                })
        except Exception:
            pass

        # Equipment maintenance
        try:
            from floor_app.operations.qrcodes.models import Equipment
            today = timezone.now().date()
            overdue_maintenance = Equipment.objects.filter(
                next_maintenance_date__lt=today
            ).count()
            if overdue_maintenance > 0:
                alerts.append({
                    'module': 'qrcodes',
                    'severity': 'danger',
                    'message': f'{overdue_maintenance} equipment overdue for maintenance',
                    'count': overdue_maintenance
                })
        except Exception:
            pass

        return alerts

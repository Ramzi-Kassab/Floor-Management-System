"""
Planning Service

Provides planning and forecasting capabilities across modules.
"""

from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from datetime import timedelta, datetime


class PlanningService:
    """
    Central service for planning and resource forecasting.
    """

    @classmethod
    def get_material_requirements(cls, days_ahead=30):
        """
        Get material requirements for upcoming production.

        Returns materials needed based on:
        - Scheduled production batches
        - BOMs for planned jobs
        - Current stock levels
        """
        try:
            from floor_app.operations.production.models import BatchOrder, JobCard
            from floor_app.operations.inventory.models import BillOfMaterialLine, InventoryStock

            today = timezone.now().date()
            end_date = today + timedelta(days=days_ahead)

            # Get upcoming job cards
            upcoming_jobs = JobCard.objects.filter(
                status__in=['PLANNED', 'SCHEDULED'],
                planned_start_date__gte=today,
                planned_start_date__lte=end_date
            )

            material_needs = {}

            for job in upcoming_jobs:
                if job.bom_id:
                    bom_lines = BillOfMaterialLine.objects.filter(bom_id=job.bom_id)
                    for line in bom_lines:
                        item_id = line.item_id
                        qty_needed = float(line.quantity * job.quantity)

                        if item_id not in material_needs:
                            material_needs[item_id] = {
                                'item_id': item_id,
                                'total_required': 0,
                                'jobs': []
                            }

                        material_needs[item_id]['total_required'] += qty_needed
                        material_needs[item_id]['jobs'].append({
                            'job_number': job.job_number,
                            'quantity': qty_needed,
                            'date': job.planned_start_date
                        })

            # Check current stock
            result = []
            for item_id, data in material_needs.items():
                stock = InventoryStock.objects.filter(item_id=item_id).first()
                current_qty = float(stock.qty_on_hand) if stock else 0
                shortfall = max(0, data['total_required'] - current_qty)

                result.append({
                    'item_id': item_id,
                    'total_required': data['total_required'],
                    'current_stock': current_qty,
                    'shortfall': shortfall,
                    'needs_purchase': shortfall > 0,
                    'jobs': data['jobs']
                })

            return sorted(result, key=lambda x: x['shortfall'], reverse=True)

        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_capacity_forecast(cls, days_ahead=30):
        """
        Forecast production capacity utilization.
        """
        try:
            from floor_app.operations.production.models import JobCard
            from floor_app.operations.hr.models import HREmployee

            today = timezone.now().date()

            # Get active operators
            total_operators = HREmployee.objects.filter(
                status='ACTIVE',
                position__name__icontains='operator'
            ).count()

            # Assume 8 hours per day per operator
            daily_capacity_hours = total_operators * 8

            # Get scheduled jobs
            forecast = []
            for i in range(days_ahead):
                date = today + timedelta(days=i)
                jobs = JobCard.objects.filter(
                    planned_start_date__lte=date,
                    planned_end_date__gte=date,
                    status__in=['PLANNED', 'SCHEDULED', 'IN_PROGRESS']
                )

                # Estimate hours needed (placeholder - would be from routing)
                estimated_hours = jobs.count() * 4  # 4 hours per job average

                utilization = 0
                if daily_capacity_hours > 0:
                    utilization = min(100, (estimated_hours / daily_capacity_hours) * 100)

                forecast.append({
                    'date': date,
                    'jobs_count': jobs.count(),
                    'estimated_hours': estimated_hours,
                    'available_hours': daily_capacity_hours,
                    'utilization_percentage': round(utilization, 2)
                })

            return forecast

        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_procurement_plan(cls):
        """
        Get procurement planning recommendations.
        """
        try:
            from floor_app.operations.purchasing.models import SupplierItem
            from floor_app.operations.inventory.models import InventoryStock

            recommendations = []

            # Find items needing reorder
            low_stock_items = InventoryStock.objects.filter(
                qty_on_hand__lte=F('reorder_point')
            )

            for stock in low_stock_items:
                # Find preferred supplier
                supplier_item = SupplierItem.objects.filter(
                    item_id=stock.item_id,
                    is_preferred=True,
                    is_active=True
                ).first()

                if not supplier_item:
                    supplier_item = SupplierItem.objects.filter(
                        item_id=stock.item_id,
                        is_active=True
                    ).first()

                reorder_qty = float(stock.reorder_qty) if stock.reorder_qty else 0
                if reorder_qty == 0:
                    reorder_qty = float(stock.reorder_point * 2)

                recommendations.append({
                    'item_id': stock.item_id,
                    'current_stock': float(stock.qty_on_hand),
                    'reorder_point': float(stock.reorder_point),
                    'recommended_qty': reorder_qty,
                    'supplier': {
                        'id': supplier_item.supplier_id if supplier_item else None,
                        'code': supplier_item.supplier.code if supplier_item else 'Unknown',
                        'lead_time_days': supplier_item.lead_time_days if supplier_item else 0,
                        'unit_price': float(supplier_item.unit_price) if supplier_item else 0,
                    } if supplier_item else None,
                    'estimated_cost': reorder_qty * float(supplier_item.unit_price) if supplier_item else 0,
                    'priority': 'HIGH' if stock.qty_on_hand <= 0 else 'MEDIUM'
                })

            return sorted(recommendations, key=lambda x: x['priority'])

        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def get_workforce_planning(cls):
        """
        Workforce planning and availability.
        """
        try:
            from floor_app.operations.hr.models import (
                HREmployee, LeaveRequest, AttendanceRecord
            )

            today = timezone.now().date()
            week_ahead = today + timedelta(days=7)

            total_active = HREmployee.objects.filter(status='ACTIVE').count()

            # Get planned leaves for next week
            upcoming_leaves = LeaveRequest.objects.filter(
                status='APPROVED',
                start_date__lte=week_ahead,
                end_date__gte=today
            ).values('start_date', 'end_date').distinct()

            daily_availability = []
            for i in range(7):
                date = today + timedelta(days=i)
                on_leave = LeaveRequest.objects.filter(
                    status='APPROVED',
                    start_date__lte=date,
                    end_date__gte=date
                ).count()

                available = total_active - on_leave
                daily_availability.append({
                    'date': date,
                    'total_employees': total_active,
                    'on_leave': on_leave,
                    'available': available,
                    'availability_percentage': round((available / total_active) * 100, 2) if total_active > 0 else 0
                })

            return {
                'total_active_employees': total_active,
                'daily_forecast': daily_availability,
                'upcoming_leaves': list(upcoming_leaves)
            }

        except Exception as e:
            return {'error': str(e)}

"""
Business logic services for Maintenance module.
"""
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal


class MaintenanceService:
    """Service for maintenance operations."""

    @staticmethod
    def get_dashboard_stats():
        """Get key metrics for maintenance dashboard."""
        from .models import Asset, WorkOrder, PMSchedule, DowntimeEvent

        today = timezone.now().date()

        # Asset stats
        total_assets = Asset.objects.filter(is_deleted=False).count()
        assets_under_maintenance = Asset.objects.filter(
            is_deleted=False, status='UNDER_MAINTENANCE'
        ).count()
        critical_assets = Asset.objects.filter(
            is_deleted=False, criticality='CRITICAL'
        ).count()

        # Work order stats
        open_work_orders = WorkOrder.objects.filter(
            is_deleted=False,
            status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_PARTS']
        ).count()

        overdue_work_orders = WorkOrder.objects.filter(
            is_deleted=False,
            status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS'],
            planned_end__lt=today
        ).count()

        # PM stats
        overdue_pms = PMSchedule.objects.filter(
            is_active=True,
            next_due_date__lt=today
        ).count()

        upcoming_pms = PMSchedule.objects.filter(
            is_active=True,
            next_due_date__gte=today,
            next_due_date__lte=today + timedelta(days=7)
        ).count()

        # Downtime stats (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_downtime = DowntimeEvent.objects.filter(
            start_time__gte=thirty_days_ago
        ).aggregate(
            total_hours=Sum('duration_minutes') / 60.0,
            event_count=Count('id')
        )

        return {
            'total_assets': total_assets,
            'assets_under_maintenance': assets_under_maintenance,
            'critical_assets': critical_assets,
            'open_work_orders': open_work_orders,
            'overdue_work_orders': overdue_work_orders,
            'overdue_pms': overdue_pms,
            'upcoming_pms': upcoming_pms,
            'recent_downtime_hours': round(recent_downtime['total_hours'] or 0, 1),
            'recent_downtime_events': recent_downtime['event_count'] or 0,
        }

    @staticmethod
    def get_assets_by_status():
        """Get asset count by status for chart."""
        from .models import Asset
        return Asset.objects.filter(is_deleted=False).values(
            'status'
        ).annotate(count=Count('id')).order_by('status')

    @staticmethod
    def get_work_orders_by_type():
        """Get work order count by type for chart."""
        from .models import WorkOrder
        return WorkOrder.objects.filter(
            is_deleted=False
        ).values('work_order_type').annotate(count=Count('id'))

    @staticmethod
    def get_recent_work_orders(limit=10):
        """Get most recent work orders."""
        from .models import WorkOrder
        return WorkOrder.objects.filter(
            is_deleted=False
        ).select_related('asset', 'assigned_to').order_by('-created_at')[:limit]

    @staticmethod
    def convert_request_to_work_order(request_obj, user=None):
        """Convert approved maintenance request to work order."""
        from .models import WorkOrder

        if request_obj.status != 'APPROVED':
            raise ValueError("Only approved requests can be converted to work orders")

        work_order = WorkOrder.objects.create(
            asset=request_obj.asset,
            title=request_obj.title,
            description=request_obj.description,
            work_order_type='CORRECTIVE',
            priority=request_obj.priority,
            status='PLANNED',
            source_request=request_obj,
            created_by=user,
        )

        request_obj.status = 'CONVERTED_TO_WO'
        request_obj.converted_work_order = work_order
        request_obj.save()

        return work_order

    @staticmethod
    def generate_pm_tasks(days_ahead=30):
        """Generate PM tasks for upcoming schedules."""
        from .models import PMSchedule, PMTask

        today = timezone.now().date()
        cutoff = today + timedelta(days=days_ahead)

        schedules = PMSchedule.objects.filter(
            is_active=True,
            next_due_date__lte=cutoff
        ).select_related('asset', 'pm_template')

        created_count = 0
        for schedule in schedules:
            # Check if task already exists for this schedule and date
            existing = PMTask.objects.filter(
                schedule=schedule,
                scheduled_date=schedule.next_due_date
            ).exists()

            if not existing:
                PMTask.objects.create(
                    schedule=schedule,
                    scheduled_date=schedule.next_due_date,
                    status='SCHEDULED'
                )
                created_count += 1

        return created_count


class DowntimeService:
    """Service for downtime and impact analysis."""

    @staticmethod
    def get_downtime_summary(asset=None, start_date=None, end_date=None):
        """Get downtime statistics for reporting."""
        from .models import DowntimeEvent

        queryset = DowntimeEvent.objects.all()

        if asset:
            queryset = queryset.filter(asset=asset)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)

        summary = queryset.aggregate(
            total_events=Count('id'),
            total_duration_minutes=Sum('duration_minutes'),
            avg_duration_minutes=Avg('duration_minutes'),
            planned_events=Count('id', filter=Q(is_planned=True)),
            unplanned_events=Count('id', filter=Q(is_planned=False)),
        )

        # Add calculated fields
        total_mins = summary['total_duration_minutes'] or 0
        summary['total_hours'] = round(total_mins / 60, 2)
        summary['avg_hours'] = round((summary['avg_duration_minutes'] or 0) / 60, 2)

        return summary

    @staticmethod
    def get_downtime_by_reason(start_date=None, end_date=None):
        """Get downtime breakdown by reason category."""
        from .models import DowntimeEvent

        queryset = DowntimeEvent.objects.all()

        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)

        return queryset.values('reason_category').annotate(
            count=Count('id'),
            total_minutes=Sum('duration_minutes')
        ).order_by('-total_minutes')

    @staticmethod
    def get_production_impact_summary(start_date=None, end_date=None):
        """Get financial impact summary from downtime."""
        from .models import ProductionImpact, LostSalesRecord

        # Production impact
        impact_query = ProductionImpact.objects.all()
        if start_date:
            impact_query = impact_query.filter(created_at__gte=start_date)
        if end_date:
            impact_query = impact_query.filter(created_at__lte=end_date)

        impact_summary = impact_query.aggregate(
            total_delay_minutes=Sum('delay_minutes'),
            total_revenue_at_risk=Sum('lost_or_delayed_revenue'),
            confirmed_count=Count('id', filter=Q(is_revenue_confirmed=True)),
        )

        # Lost sales
        lost_query = LostSalesRecord.objects.all()
        if start_date:
            lost_query = lost_query.filter(confirmed_at__gte=start_date)
        if end_date:
            lost_query = lost_query.filter(confirmed_at__lte=end_date)

        lost_summary = lost_query.aggregate(
            total_lost=Sum('revenue_lost'),
            total_delayed=Sum('revenue_delayed'),
            record_count=Count('id'),
        )

        return {
            'total_delay_hours': round((impact_summary['total_delay_minutes'] or 0) / 60, 2),
            'total_revenue_at_risk': impact_summary['total_revenue_at_risk'] or Decimal('0'),
            'confirmed_impacts': impact_summary['confirmed_count'] or 0,
            'total_lost_revenue': lost_summary['total_lost'] or Decimal('0'),
            'total_delayed_revenue': lost_summary['total_delayed'] or Decimal('0'),
            'lost_sales_records': lost_summary['record_count'] or 0,
        }

    @staticmethod
    def get_top_downtime_assets(limit=10, days=30):
        """Get assets with most downtime."""
        from .models import DowntimeEvent

        cutoff = timezone.now() - timedelta(days=days)

        return DowntimeEvent.objects.filter(
            start_time__gte=cutoff
        ).values(
            'asset__asset_code', 'asset__name'
        ).annotate(
            total_minutes=Sum('duration_minutes'),
            event_count=Count('id')
        ).order_by('-total_minutes')[:limit]


class AssetService:
    """Service for asset management operations."""

    @staticmethod
    def get_asset_health_score(asset):
        """Calculate health score based on maintenance history."""
        from .models import WorkOrder, PMTask

        score = 100

        # Deduct for overdue PMs
        overdue_pms = asset.pm_schedules.filter(
            is_active=True,
            next_due_date__lt=timezone.now().date()
        ).count()
        score -= overdue_pms * 10

        # Deduct for recent breakdowns (last 90 days)
        ninety_days_ago = timezone.now() - timedelta(days=90)
        breakdown_count = asset.work_orders.filter(
            work_order_type='CORRECTIVE',
            created_at__gte=ninety_days_ago
        ).count()
        score -= breakdown_count * 15

        # Deduct for open work orders
        open_wos = asset.work_orders.filter(
            status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_PARTS']
        ).count()
        score -= open_wos * 5

        return max(0, min(100, score))

    @staticmethod
    def get_warranty_expiring_assets(days=30):
        """Get assets with warranty expiring soon."""
        from .models import Asset

        today = timezone.now().date()
        cutoff = today + timedelta(days=days)

        return Asset.objects.filter(
            is_deleted=False,
            warranty_expires__gte=today,
            warranty_expires__lte=cutoff
        ).order_by('warranty_expires')

    @staticmethod
    def generate_qr_token(asset):
        """Generate unique QR token for asset."""
        import uuid
        if not asset.qr_token:
            asset.qr_token = str(uuid.uuid4())[:12].upper()
            asset.save(update_fields=['qr_token'])
        return asset.qr_token

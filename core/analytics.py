"""
Analytics and Business Intelligence for Floor Management System.

Features:
- KPI tracking and trends
- Predictive analytics helpers
- Performance metrics
- Custom dashboards
- Trend analysis
"""

from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, F, Q, Window
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
import statistics


class KPITracker:
    """Track Key Performance Indicators."""
    
    @staticmethod
    def calculate_kpi(model, metric_field, filters=None, period_days=30):
        """Calculate KPI for a model and metric."""
        queryset = model.objects.all()
        
        if filters:
            queryset = queryset.filter(**filters)
            
        # Get current period
        current_end = timezone.now()
        current_start = current_end - timedelta(days=period_days)
        
        current_data = queryset.filter(
            created_at__gte=current_start,
            created_at__lte=current_end
        ).aggregate(
            total=Count('id'),
            avg=Avg(metric_field) if metric_field else None,
            sum=Sum(metric_field) if metric_field else None
        )
        
        # Get previous period for comparison
        previous_end = current_start
        previous_start = previous_end - timedelta(days=period_days)
        
        previous_data = queryset.filter(
            created_at__gte=previous_start,
            created_at__lte=previous_end
        ).aggregate(
            total=Count('id'),
            avg=Avg(metric_field) if metric_field else None,
            sum=Sum(metric_field) if metric_field else None
        )
        
        # Calculate change
        change = {}
        for key in current_data:
            curr_val = current_data[key] or 0
            prev_val = previous_data[key] or 0
            
            if prev_val > 0:
                change[key] = ((curr_val - prev_val) / prev_val) * 100
            else:
                change[key] = 100 if curr_val > 0 else 0
                
        return {
            'current': current_data,
            'previous': previous_data,
            'change_percent': change,
            'period_days': period_days
        }
    
    @staticmethod
    def get_trend(model, date_field='created_at', period_days=30, interval='day'):
        """Get trend data for visualization."""
        queryset = model.objects.all()
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        queryset = queryset.filter(**{
            f'{date_field}__gte': start_date,
            f'{date_field}__lte': end_date
        })
        
        # Truncate by interval
        trunc_func = TruncDate if interval == 'day' else TruncMonth
        
        trend_data = queryset.annotate(
            period=trunc_func(date_field)
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
        
        return list(trend_data)


class PerformanceMetrics:
    """Calculate performance metrics."""
    
    @staticmethod
    def calculate_efficiency(completed, total):
        """Calculate efficiency percentage."""
        if total == 0:
            return 0
        return (completed / total) * 100
        
    @staticmethod
    def calculate_growth_rate(current, previous):
        """Calculate growth rate."""
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
        
    @staticmethod
    def moving_average(data_points, window=7):
        """Calculate moving average."""
        if len(data_points) < window:
            return statistics.mean(data_points) if data_points else 0
            
        return statistics.mean(data_points[-window:])
        
    @staticmethod
    def forecast_linear(historical_data, periods=7):
        """Simple linear forecast."""
        if len(historical_data) < 2:
            return []
            
        # Calculate trend
        x_vals = list(range(len(historical_data)))
        y_vals = historical_data
        
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(y_vals)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if denominator == 0:
            return [y_mean] * periods
            
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Generate forecast
        forecast = []
        for i in range(periods):
            x = len(historical_data) + i
            y = slope * x + intercept
            forecast.append(max(0, y))  # No negative forecasts
            
        return forecast

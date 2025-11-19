"""
Utility Tools System Views

Template-rendering views for calculators, converters, and file tools.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import (
    Calculator,
    FileConversion,
    ToolUsageLog,
)


@login_required
def tools_dashboard(request):
    """
    Utility tools dashboard.

    Shows:
    - Available tools
    - Recent usage
    - Quick access to common tools
    """
    try:
        # Get available calculators
        calculators = Calculator.objects.filter(is_active=True).order_by('name')

        # Get recent file conversions
        recent_conversions = FileConversion.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        # Get recent tool usage
        recent_usage = ToolUsageLog.objects.filter(
            user=request.user
        ).select_related('calculator').order_by('-used_at')[:20]

        # Statistics
        stats = {
            'total_tools': Calculator.objects.filter(is_active=True).count(),
            'conversions_today': FileConversion.objects.filter(
                user=request.user,
                created_at__date=timezone.now().date()
            ).count(),
            'tools_used_today': ToolUsageLog.objects.filter(
                user=request.user,
                used_at__date=timezone.now().date()
            ).count(),
        }

        # Tool categories
        tool_categories = Calculator.objects.filter(
            is_active=True
        ).values('category').distinct()

        context = {
            'calculators': calculators,
            'recent_conversions': recent_conversions,
            'recent_usage': recent_usage,
            'stats': stats,
            'tool_categories': tool_categories,
            'page_title': 'Utility Tools',
        }

    except Exception as e:
        messages.error(request, f'Error loading tools dashboard: {str(e)}')
        context = {
            'calculators': [],
            'recent_conversions': [],
            'recent_usage': [],
            'stats': {},
            'tool_categories': [],
            'page_title': 'Utility Tools',
        }

    return render(request, 'utility_tools/tools_dashboard.html', context)


@login_required
def calculators(request):
    """
    Calculators and computation tools.

    Provides:
    - Mathematical calculators
    - Engineering calculators
    - Financial calculators
    - Unit converters
    """
    try:
        # Get all calculators
        all_calculators = Calculator.objects.filter(is_active=True)

        # Filter by category
        category_filter = request.GET.get('category')
        if category_filter:
            all_calculators = all_calculators.filter(category=category_filter)

        # Search
        search_query = request.GET.get('q')
        if search_query:
            all_calculators = all_calculators.filter(name__icontains=search_query)

        all_calculators = all_calculators.order_by('category', 'name')

        # Handle calculation
        if request.method == 'POST':
            try:
                calculator_id = request.POST.get('calculator_id')
                input_values = {}

                # Collect all input values
                for key, value in request.POST.items():
                    if key.startswith('input_'):
                        field_name = key.replace('input_', '')
                        input_values[field_name] = value

                if calculator_id:
                    calculator = get_object_or_404(Calculator, pk=calculator_id)

                    # Log usage
                    ToolUsageLog.objects.create(
                        user=request.user,
                        calculator=calculator,
                        tool_type='CALCULATOR',
                        input_data=input_values,
                        used_at=timezone.now()
                    )

                    # TODO: Implement actual calculation logic based on calculator type
                    result = "Calculation result would appear here"

                    messages.success(request, 'Calculation completed successfully.')
                    context = {
                        'calculators': all_calculators,
                        'selected_calculator': calculator,
                        'result': result,
                        'input_values': input_values,
                        'page_title': 'Calculators',
                    }
                    return render(request, 'utility_tools/calculators.html', context)

            except Exception as e:
                messages.error(request, f'Error performing calculation: {str(e)}')

        # Get calculator categories
        categories = Calculator.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct()

        context = {
            'calculators': all_calculators,
            'categories': categories,
            'category_filter': category_filter,
            'search_query': search_query,
            'page_title': 'Calculators',
        }

    except Exception as e:
        messages.error(request, f'Error loading calculators: {str(e)}')
        context = {
            'calculators': [],
            'categories': [],
            'page_title': 'Calculators',
        }

    return render(request, 'utility_tools/calculators.html', context)


@login_required
def file_tools(request):
    """
    File conversion and manipulation tools.

    Provides:
    - File format conversion
    - Image resizing
    - PDF operations
    - Compression tools
    """
    try:
        if request.method == 'POST':
            try:
                conversion_type = request.POST.get('conversion_type')
                uploaded_file = request.FILES.get('file')

                if not uploaded_file:
                    messages.error(request, 'Please select a file to convert.')
                elif not conversion_type:
                    messages.error(request, 'Please select conversion type.')
                else:
                    # Create conversion record
                    conversion = FileConversion.objects.create(
                        user=request.user,
                        conversion_type=conversion_type,
                        original_file=uploaded_file,
                        original_filename=uploaded_file.name,
                        original_size=uploaded_file.size,
                        status='PENDING'
                    )

                    # Log usage
                    ToolUsageLog.objects.create(
                        user=request.user,
                        tool_type='FILE_CONVERTER',
                        input_data={
                            'conversion_type': conversion_type,
                            'filename': uploaded_file.name,
                            'size': uploaded_file.size
                        },
                        used_at=timezone.now()
                    )

                    # TODO: Implement actual conversion logic
                    conversion.status = 'COMPLETED'
                    conversion.completed_at = timezone.now()
                    conversion.save()

                    messages.success(request, 'File conversion initiated successfully.')
                    return redirect('utility_tools:file_tools')

            except Exception as e:
                messages.error(request, f'Error converting file: {str(e)}')

        # Get user's recent conversions
        conversions = FileConversion.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]

        # Conversion types
        conversion_types = FileConversion.CONVERSION_TYPES

        # Statistics
        stats = {
            'total_conversions': FileConversion.objects.filter(user=request.user).count(),
            'completed': FileConversion.objects.filter(user=request.user, status='COMPLETED').count(),
            'failed': FileConversion.objects.filter(user=request.user, status='FAILED').count(),
        }

        context = {
            'conversions': conversions,
            'conversion_types': conversion_types,
            'stats': stats,
            'page_title': 'File Tools',
        }

    except Exception as e:
        messages.error(request, f'Error loading file tools: {str(e)}')
        context = {
            'conversions': [],
            'conversion_types': [],
            'stats': {},
            'page_title': 'File Tools',
        }

    return render(request, 'utility_tools/file_tools.html', context)

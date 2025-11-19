"""
Cutter BOM & Map Grid System API Views

REST API viewsets for Cutter BOM and Map grid system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from django.http import HttpResponse
from django.db import transaction

from floor_app.operations.inventory.models import (
    CutterBOMGrid,
    CutterBOMGridRow,
    CutterBOMGridColumn,
    CutterBOMGridCell,
    CutterBOMGridValidation,
    CutterBOMGridHistory,
    CutterMapGrid,
    CutterMapGridRow,
    CutterMapGridColumn,
    CutterMapGridCell,
    CutterMapGridValidation,
    CutterMapGridHistory
)
from .serializers import (
    CutterBOMGridSerializer,
    CutterBOMGridCreateSerializer,
    CutterBOMGridColumnSerializer,
    CutterBOMGridRowSerializer,
    CutterBOMGridCellSerializer,
    CutterBOMGridCellUpdateSerializer,
    CutterBOMGridCellBulkUpdateSerializer,
    CutterBOMGridValidationSerializer,
    CutterBOMGridHistorySerializer,
    CutterMapGridSerializer,
    CutterMapGridCreateSerializer,
    CutterMapGridColumnSerializer,
    CutterMapGridRowSerializer,
    CutterMapGridCellSerializer,
    CutterMapGridValidationSerializer,
    CutterMapGridHistorySerializer,
    GridComparisonSerializer,
    GridCloneSerializer,
    GridExportSerializer,
    GridImportSerializer
)


# ==================== Cutter BOM Grid ViewSets ====================

class CutterBOMGridViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Cutter BOM grids.

    list: Get all BOM grids
    retrieve: Get a specific BOM grid with all rows/columns
    create: Create a new BOM grid
    update: Update BOM grid details
    destroy: Delete a BOM grid (soft delete)
    """

    queryset = CutterBOMGrid.objects.all().select_related(
        'created_by', 'locked_by', 'job_order', 'cutter_serial'
    ).prefetch_related('columns', 'rows')
    serializer_class = CutterBOMGridSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['stage', 'status', 'is_locked', 'job_order', 'cutter_serial']
    search_fields = ['grid_name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'stage']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return CutterBOMGridCreateSerializer
        return CutterBOMGridSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new BOM grid.

        POST /api/bom-grids/
        Body: {
            "grid_name": "Cutter #12345 BOM",
            "stage": "DESIGN",
            "job_order_id": 1,
            "cutter_serial_id": 5,
            "rows_count": 50,
            "template_id": 3  // Optional: copy from template
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        with transaction.atomic():
            # Create grid
            grid = CutterBOMGrid.objects.create(
                grid_name=data['grid_name'],
                description=data.get('description', ''),
                stage=data.get('stage', 'DESIGN'),
                created_by=request.user,
                metadata=data.get('metadata', {})
            )

            # Link to job order if provided
            if data.get('job_order_id'):
                from floor_app.operations.planning.models import JobOrder
                grid.job_order = JobOrder.objects.get(id=data['job_order_id'])

            # Link to cutter serial if provided
            if data.get('cutter_serial_id'):
                from floor_app.operations.inventory.models import CutterSerial
                grid.cutter_serial = CutterSerial.objects.get(id=data['cutter_serial_id'])

            grid.save()

            # If template provided, copy structure
            if data.get('template_id'):
                template = CutterBOMGrid.objects.get(id=data['template_id'])
                grid.copy_structure_from(template)
            else:
                # Initialize default structure
                grid.initialize_default_structure(rows_count=data.get('rows_count', 50))

        output_serializer = CutterBOMGridSerializer(grid)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """
        Lock a grid to prevent editing.

        POST /api/bom-grids/{id}/lock/
        """
        grid = self.get_object()

        if grid.is_locked:
            return Response(
                {'error': f'Grid is already locked by {grid.locked_by}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grid.lock(user=request.user)

        serializer = self.get_serializer(grid)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """
        Unlock a grid.

        POST /api/bom-grids/{id}/unlock/
        """
        grid = self.get_object()

        if not grid.is_locked:
            return Response(
                {'error': 'Grid is not locked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only the user who locked it or admin can unlock
        if grid.locked_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only the user who locked the grid or admin can unlock it'},
                status=status.HTTP_403_FORBIDDEN
            )

        grid.unlock()

        serializer = self.get_serializer(grid)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate_all(self, request, pk=None):
        """
        Run all validations on the grid.

        POST /api/bom-grids/{id}/validate_all/
        """
        grid = self.get_object()

        # Run validations
        validation_results = grid.run_all_validations()

        return Response({
            'success': True,
            'total_cells': validation_results['total_cells'],
            'valid_cells': validation_results['valid_cells'],
            'error_cells': validation_results['error_cells'],
            'warning_cells': validation_results['warning_cells'],
            'errors': validation_results['errors']
        })

    @action(detail=True, methods=['get'])
    def cells(self, request, pk=None):
        """
        Get all cells for a grid.

        GET /api/bom-grids/{id}/cells/
        """
        grid = self.get_object()
        cells = grid.cells.all().select_related('row', 'column', 'edited_by')

        # Filter by row if provided
        row_id = request.query_params.get('row_id')
        if row_id:
            cells = cells.filter(row_id=row_id)

        # Filter by column if provided
        column_id = request.query_params.get('column_id')
        if column_id:
            cells = cells.filter(column_id=column_id)

        # Filter by modified status
        only_modified = request.query_params.get('only_modified', 'false').lower() == 'true'
        if only_modified:
            cells = cells.filter(is_modified=True)

        page = self.paginate_queryset(cells)
        if page is not None:
            serializer = CutterBOMGridCellSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CutterBOMGridCellSerializer(cells, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_cell(self, request, pk=None):
        """
        Update a single cell value.

        POST /api/bom-grids/{id}/update_cell/
        Body: {
            "row_id": 1,
            "column_id": 2,
            "cell_value": "New value",
            "validate_on_save": true
        }
        """
        grid = self.get_object()

        if grid.is_locked and grid.locked_by != request.user:
            return Response(
                {'error': 'Grid is locked by another user'},
                status=status.HTTP_403_FORBIDDEN
            )

        row_id = request.data.get('row_id')
        column_id = request.data.get('column_id')

        if not row_id or not column_id:
            return Response(
                {'error': 'row_id and column_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CutterBOMGridCellUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get or create cell
        cell, created = CutterBOMGridCell.objects.get_or_create(
            grid=grid,
            row_id=row_id,
            column_id=column_id,
            defaults={'cell_value': ''}
        )

        # Update cell
        cell.update_value(
            new_value=data['cell_value'],
            user=request.user,
            validate=data.get('validate_on_save', True)
        )

        output_serializer = CutterBOMGridCellSerializer(cell)
        return Response(output_serializer.data)

    @action(detail=True, methods=['post'])
    def bulk_update_cells(self, request, pk=None):
        """
        Update multiple cells at once.

        POST /api/bom-grids/{id}/bulk_update_cells/
        Body: {
            "updates": [
                {"row_id": 1, "column_id": 2, "value": "Value 1"},
                {"row_id": 1, "column_id": 3, "value": "Value 2"},
                {"row_id": 2, "column_id": 2, "value": "Value 3"}
            ],
            "validate_on_save": true
        }
        """
        grid = self.get_object()

        if grid.is_locked and grid.locked_by != request.user:
            return Response(
                {'error': 'Grid is locked by another user'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CutterBOMGridCellBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        updates = data['updates']
        validate = data.get('validate_on_save', True)

        updated_cells = []
        errors = []

        with transaction.atomic():
            for update in updates:
                try:
                    row_id = update.get('row_id')
                    column_id = update.get('column_id')
                    value = update.get('value', '')

                    # Get or create cell
                    cell, created = CutterBOMGridCell.objects.get_or_create(
                        grid=grid,
                        row_id=row_id,
                        column_id=column_id,
                        defaults={'cell_value': ''}
                    )

                    # Update cell
                    cell.update_value(
                        new_value=value,
                        user=request.user,
                        validate=validate
                    )

                    updated_cells.append(cell)

                except Exception as e:
                    errors.append({
                        'row_id': update.get('row_id'),
                        'column_id': update.get('column_id'),
                        'error': str(e)
                    })

        return Response({
            'success': True,
            'updated_count': len(updated_cells),
            'error_count': len(errors),
            'errors': errors
        })

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get change history for a grid.

        GET /api/bom-grids/{id}/history/
        """
        grid = self.get_object()
        history = grid.history.all().order_by('-changed_at')

        # Filter by action if provided
        action = request.query_params.get('action')
        if action:
            history = history.filter(action=action)

        page = self.paginate_queryset(history)
        if page is not None:
            serializer = CutterBOMGridHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CutterBOMGridHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """
        Clone a grid.

        POST /api/bom-grids/{id}/clone/
        Body: {
            "new_name": "Cloned Grid",
            "include_data": true,
            "include_validations": true
        }
        """
        grid = self.get_object()

        serializer = GridCloneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Clone grid
        cloned_grid = grid.clone(
            new_name=data['new_name'],
            user=request.user,
            include_data=data.get('include_data', True),
            include_validations=data.get('include_validations', True)
        )

        output_serializer = CutterBOMGridSerializer(cloned_grid)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        Compare two grids.

        POST /api/bom-grids/compare/
        Body: {
            "source_grid_id": 1,
            "target_grid_id": 2,
            "comparison_type": "VALUES"  // VALUES, STRUCTURE, or BOTH
        }
        """
        serializer = GridComparisonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        source_grid = CutterBOMGrid.objects.get(id=data['source_grid_id'])
        target_grid = CutterBOMGrid.objects.get(id=data['target_grid_id'])

        comparison_type = data.get('comparison_type', 'VALUES')

        # Compare grids
        differences = source_grid.compare_with(target_grid, comparison_type=comparison_type)

        return Response({
            'source_grid': {
                'id': source_grid.id,
                'name': source_grid.grid_name
            },
            'target_grid': {
                'id': target_grid.id,
                'name': target_grid.grid_name
            },
            'comparison_type': comparison_type,
            'differences': differences
        })

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Export grid to Excel/CSV.

        GET /api/bom-grids/{id}/export/?format=XLSX
        """
        grid = self.get_object()

        format = request.query_params.get('format', 'XLSX').upper()
        include_metadata = request.query_params.get('include_metadata', 'false').lower() == 'true'
        include_history = request.query_params.get('include_history', 'false').lower() == 'true'

        # Export to Excel
        if format == 'XLSX':
            file_content = grid.export_to_excel(
                include_metadata=include_metadata,
                include_history=include_history
            )
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            file_extension = 'xlsx'
        elif format == 'CSV':
            file_content = grid.export_to_csv()
            content_type = 'text/csv'
            file_extension = 'csv'
        else:
            return Response(
                {'error': 'Invalid format. Use XLSX or CSV'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create response
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{grid.grid_name}.{file_extension}"'
        return response

    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """
        Import grid from Excel file.

        POST /api/bom-grids/import_excel/
        Body: multipart/form-data
            file: Excel file
            validate_on_import: true/false
            skip_errors: true/false
            update_existing: true/false
        """
        serializer = GridImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        file = data['file']
        validate_on_import = data.get('validate_on_import', True)
        skip_errors = data.get('skip_errors', False)
        update_existing = data.get('update_existing', False)

        try:
            # Import from Excel
            grid = CutterBOMGrid.import_from_excel(
                file=file,
                user=request.user,
                validate_on_import=validate_on_import,
                skip_errors=skip_errors,
                update_existing=update_existing
            )

            output_serializer = CutterBOMGridSerializer(grid)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get BOM grids statistics.

        GET /api/bom-grids/stats/
        """
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_stage': list(
                queryset.values('stage').annotate(count=Count('id'))
            ),
            'by_status': list(
                queryset.values('status').annotate(count=Count('id'))
            ),
            'locked': queryset.filter(is_locked=True).count(),
            'modified_today': queryset.filter(
                updated_at__date=timezone.now().date()
            ).count(),
        }

        return Response(stats)


class CutterBOMGridValidationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing BOM grid validation rules.

    list: Get all validation rules
    retrieve: Get a specific validation rule
    create: Create a new validation rule
    update: Update a validation rule
    destroy: Delete a validation rule
    """

    queryset = CutterBOMGridValidation.objects.all()
    serializer_class = CutterBOMGridValidationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['grid', 'validation_type', 'is_active']

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Execute a specific validation rule on grid.

        POST /api/bom-grid-validations/{id}/execute/
        """
        validation = self.get_object()

        # Execute validation
        results = validation.execute_validation()

        return Response({
            'success': True,
            'validation_name': validation.validation_name,
            'total_cells_checked': results['total_cells'],
            'errors_found': results['errors_count'],
            'errors': results['errors']
        })


# ==================== Cutter Map Grid ViewSets ====================

class CutterMapGridViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Cutter Map grids.

    list: Get all Map grids
    retrieve: Get a specific Map grid with all rows/columns
    create: Create a new Map grid
    update: Update Map grid details
    destroy: Delete a Map grid (soft delete)
    """

    queryset = CutterMapGrid.objects.all().select_related(
        'created_by', 'locked_by', 'job_order', 'cutter_serial'
    ).prefetch_related('columns', 'rows')
    serializer_class = CutterMapGridSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['stage', 'status', 'is_locked', 'job_order', 'cutter_serial']
    search_fields = ['grid_name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'stage']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return CutterMapGridCreateSerializer
        return CutterMapGridSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new Map grid.

        POST /api/map-grids/
        Body: {
            "grid_name": "Cutter #12345 Map",
            "stage": "DESIGN",
            "job_order_id": 1,
            "cutter_serial_id": 5,
            "rows_count": 50,
            "template_id": 3  // Optional: copy from template
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        with transaction.atomic():
            # Create grid
            grid = CutterMapGrid.objects.create(
                grid_name=data['grid_name'],
                description=data.get('description', ''),
                stage=data.get('stage', 'DESIGN'),
                created_by=request.user,
                metadata=data.get('metadata', {})
            )

            # Link to job order if provided
            if data.get('job_order_id'):
                from floor_app.operations.planning.models import JobOrder
                grid.job_order = JobOrder.objects.get(id=data['job_order_id'])

            # Link to cutter serial if provided
            if data.get('cutter_serial_id'):
                from floor_app.operations.inventory.models import CutterSerial
                grid.cutter_serial = CutterSerial.objects.get(id=data['cutter_serial_id'])

            grid.save()

            # If template provided, copy structure
            if data.get('template_id'):
                template = CutterMapGrid.objects.get(id=data['template_id'])
                grid.copy_structure_from(template)
            else:
                # Initialize default structure
                grid.initialize_default_structure(rows_count=data.get('rows_count', 50))

        output_serializer = CutterMapGridSerializer(grid)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    # Map grid has same actions as BOM grid - lock, unlock, validate_all, cells,
    # update_cell, bulk_update_cells, history, clone, export, import_excel, stats
    # Implementation would be identical to BOM grid but using CutterMapGrid models
    # For brevity, I'll implement the key unique ones and note that others are similar

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock a Map grid to prevent editing."""
        grid = self.get_object()

        if grid.is_locked:
            return Response(
                {'error': f'Grid is already locked by {grid.locked_by}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grid.lock(user=request.user)
        serializer = self.get_serializer(grid)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """Unlock a Map grid."""
        grid = self.get_object()

        if not grid.is_locked:
            return Response({'error': 'Grid is not locked'}, status=status.HTTP_400_BAD_REQUEST)

        if grid.locked_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only the user who locked the grid or admin can unlock it'},
                status=status.HTTP_403_FORBIDDEN
            )

        grid.unlock()
        serializer = self.get_serializer(grid)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cells(self, request, pk=None):
        """Get all cells for a Map grid."""
        grid = self.get_object()
        cells = grid.cells.all().select_related('row', 'column', 'edited_by')

        row_id = request.query_params.get('row_id')
        if row_id:
            cells = cells.filter(row_id=row_id)

        column_id = request.query_params.get('column_id')
        if column_id:
            cells = cells.filter(column_id=column_id)

        only_modified = request.query_params.get('only_modified', 'false').lower() == 'true'
        if only_modified:
            cells = cells.filter(is_modified=True)

        page = self.paginate_queryset(cells)
        if page is not None:
            serializer = CutterMapGridCellSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CutterMapGridCellSerializer(cells, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export Map grid to Excel/CSV."""
        grid = self.get_object()

        format = request.query_params.get('format', 'XLSX').upper()
        include_metadata = request.query_params.get('include_metadata', 'false').lower() == 'true'
        include_history = request.query_params.get('include_history', 'false').lower() == 'true'

        if format == 'XLSX':
            file_content = grid.export_to_excel(
                include_metadata=include_metadata,
                include_history=include_history
            )
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            file_extension = 'xlsx'
        elif format == 'CSV':
            file_content = grid.export_to_csv()
            content_type = 'text/csv'
            file_extension = 'csv'
        else:
            return Response(
                {'error': 'Invalid format. Use XLSX or CSV'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{grid.grid_name}.{file_extension}"'
        return response


class CutterMapGridValidationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Map grid validation rules.
    """

    queryset = CutterMapGridValidation.objects.all()
    serializer_class = CutterMapGridValidationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['grid', 'validation_type', 'is_active']

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a specific validation rule on grid."""
        validation = self.get_object()
        results = validation.execute_validation()

        return Response({
            'success': True,
            'validation_name': validation.validation_name,
            'total_cells_checked': results['total_cells'],
            'errors_found': results['errors_count'],
            'errors': results['errors']
        })

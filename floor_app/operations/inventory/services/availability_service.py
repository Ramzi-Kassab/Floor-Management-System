"""
Cutter Availability Service

Smart availability display service for cutter selection in BOM/Map grids.

Features:
- Real-time availability checking
- Reclaimed cutter filtering (hide for new bits)
- Reserved quantity tracking
- Multiple view modes (summary, detailed, by location)
- Availability forecasting
"""

from typing import Dict, List, Optional, Tuple
from django.db.models import Sum, Q, F
from decimal import Decimal


class CutterAvailabilityService:
    """
    Service for checking and displaying cutter availability.

    Provides smart filtering and display options for cutter inventory.
    """

    def __init__(self, show_reclaimed: bool = False):
        """
        Initialize availability service.

        Args:
            show_reclaimed: Whether to include reclaimed cutters in availability
        """
        self.show_reclaimed = show_reclaimed

    def get_availability_for_bom(self, bom_grid) -> Dict:
        """
        Get availability for all cutter types in a BOM.

        Args:
            bom_grid: CutterBOMGridHeader instance

        Returns:
            Dict with availability info for each cutter type
        """
        from floor_app.operations.inventory.models import CutterInventorySummary

        # Get all cutter types in BOM
        cutter_types = bom_grid.cells.filter(
            cutter_type__isnull=False
        ).values_list('cutter_type_id', flat=True).distinct()

        availability = {}

        for cutter_type_id in cutter_types:
            avail_info = self._get_cutter_availability(cutter_type_id)
            if avail_info:
                availability[cutter_type_id] = avail_info

        return availability

    def get_availability_for_cell(self, cell) -> Optional[Dict]:
        """
        Get availability for a specific cell's required cutter type.

        Args:
            cell: CutterMapCell or CutterBOMGridCell instance

        Returns:
            Dict with availability info or None
        """
        cutter_type = getattr(cell, 'required_cutter_type', None) or getattr(cell, 'cutter_type', None)

        if not cutter_type:
            return None

        return self._get_cutter_availability(cutter_type.id)

    def get_availability_summary(self, cutter_type_ids: List[int]) -> Dict:
        """
        Get availability summary for multiple cutter types.

        Args:
            cutter_type_ids: List of CutterDetail IDs

        Returns:
            Dict with summary statistics
        """
        from floor_app.operations.inventory.models import CutterInventorySummary

        summaries = CutterInventorySummary.objects.filter(
            cutter_detail_id__in=cutter_type_ids
        )

        total_new = summaries.aggregate(Sum('quantity_new_good'))['quantity_new_good__sum'] or 0
        total_reclaimed = summaries.aggregate(Sum('quantity_reclaimed_good'))['quantity_reclaimed_good__sum'] or 0
        total_in_transit = summaries.aggregate(Sum('quantity_in_transit'))['quantity_in_transit__sum'] or 0
        total_reserved = summaries.aggregate(Sum('quantity_reserved'))['quantity_reserved__sum'] or 0

        if self.show_reclaimed:
            total_available = total_new + total_reclaimed
        else:
            total_available = total_new

        return {
            'total_types': len(cutter_type_ids),
            'total_available': total_available,
            'total_new': total_new,
            'total_reclaimed': total_reclaimed,
            'total_in_transit': total_in_transit,
            'total_reserved': total_reserved,
            'show_reclaimed': self.show_reclaimed,
        }

    def check_bom_feasibility(self, bom_grid) -> Tuple[bool, List[str]]:
        """
        Check if BOM can be fulfilled with current inventory.

        Args:
            bom_grid: CutterBOMGridHeader instance

        Returns:
            Tuple of (is_feasible, list_of_issues)
        """
        from floor_app.operations.inventory.models import CutterBOMSummary

        is_feasible = True
        issues = []

        # Check each cutter type in BOM
        for summary in bom_grid.summaries.all():
            cutter_type = summary.cutter_detail
            required = summary.required_quantity

            # Get availability
            avail_info = self._get_cutter_availability(cutter_type.id)

            if not avail_info:
                is_feasible = False
                issues.append(
                    f"{cutter_type}: No inventory data (need {required})"
                )
                continue

            available = avail_info['total_available']

            if available < required:
                is_feasible = False
                shortage = required - available

                # Check if in-transit will help
                if avail_info['in_transit'] >= shortage:
                    issues.append(
                        f"{cutter_type}: Short by {shortage} "
                        f"(need {required}, have {available}, "
                        f"{avail_info['in_transit']} in transit)"
                    )
                else:
                    issues.append(
                        f"{cutter_type}: Short by {shortage} "
                        f"(need {required}, have {available})"
                    )
            elif available < required * 1.2:  # Less than 20% buffer
                issues.append(
                    f"{cutter_type}: Low stock warning "
                    f"(need {required}, have {available})"
                )

        return is_feasible, issues

    def get_alternative_cutters(self, cutter_type_id: int) -> List[Dict]:
        """
        Get alternative/substitute cutter types that are in stock.

        Args:
            cutter_type_id: Primary cutter type ID

        Returns:
            List of alternative cutters with availability
        """
        from floor_app.operations.inventory.models import CutterDetail, CutterInventorySummary

        # Get the primary cutter
        try:
            primary = CutterDetail.objects.get(id=cutter_type_id)
        except CutterDetail.DoesNotExist:
            return []

        # Find similar cutters (same size, similar type)
        similar_cutters = CutterDetail.objects.filter(
            cutter_size=primary.cutter_size,
            # Could add more similarity criteria
        ).exclude(
            id=cutter_type_id
        )

        alternatives = []

        for cutter in similar_cutters:
            avail_info = self._get_cutter_availability(cutter.id)
            if avail_info and avail_info['total_available'] > 0:
                alternatives.append({
                    'cutter': cutter,
                    'availability': avail_info,
                    'similarity_score': self._calculate_similarity(primary, cutter),
                })

        # Sort by similarity score
        alternatives.sort(key=lambda x: x['similarity_score'], reverse=True)

        return alternatives

    def get_detailed_availability(
        self,
        cutter_type_id: int,
        include_locations: bool = True,
        include_serials: bool = False
    ) -> Optional[Dict]:
        """
        Get detailed availability breakdown.

        Args:
            cutter_type_id: CutterDetail ID
            include_locations: Include per-location breakdown
            include_serials: Include individual serial numbers

        Returns:
            Dict with detailed availability info
        """
        from floor_app.operations.inventory.models import (
            CutterInventorySummary,
            InventoryStock,
            SerialUnit,
        )

        # Get summary
        base_info = self._get_cutter_availability(cutter_type_id)
        if not base_info:
            return None

        detailed = {
            **base_info,
            'detailed_breakdown': {},
        }

        # Per-location breakdown
        if include_locations:
            stock_by_location = InventoryStock.objects.filter(
                item__cutter_detail_id=cutter_type_id,
                quantity_on_hand__gt=0
            ).values(
                'location__name',
                'condition_type__name'
            ).annotate(
                quantity=Sum('quantity_on_hand')
            )

            detailed['by_location'] = list(stock_by_location)

        # Individual serials
        if include_serials:
            serials = SerialUnit.objects.filter(
                item__cutter_detail_id=cutter_type_id,
                mat_state__in=['AVAILABLE', 'GOOD']
            ).select_related('location', 'condition_type').values(
                'serial_number',
                'condition_type__name',
                'location__name',
                'ownership_type__name'
            )

            detailed['serials'] = list(serials)

        return detailed

    def _get_cutter_availability(self, cutter_type_id: int) -> Optional[Dict]:
        """
        Get availability for a single cutter type.

        Args:
            cutter_type_id: CutterDetail ID

        Returns:
            Dict with availability info or None
        """
        from floor_app.operations.inventory.models import CutterInventorySummary, CutterDetail

        summary = CutterInventorySummary.objects.filter(
            cutter_detail_id=cutter_type_id
        ).select_related('cutter_detail').first()

        if not summary:
            return None

        # Calculate total available based on reclaimed filter
        if self.show_reclaimed:
            total_available = summary.quantity_new_good + summary.quantity_reclaimed_good
        else:
            total_available = summary.quantity_new_good

        # Determine status
        status = 'out_of_stock'
        if total_available > 10:
            status = 'in_stock'
        elif total_available > 0:
            status = 'low_stock'
        elif summary.quantity_in_transit > 0:
            status = 'in_transit'

        return {
            'cutter_type_id': cutter_type_id,
            'cutter_type': str(summary.cutter_detail),
            'available_new': summary.quantity_new_good,
            'available_reclaimed': summary.quantity_reclaimed_good,
            'total_available': total_available,
            'in_transit': summary.quantity_in_transit,
            'reserved': summary.quantity_reserved,
            'damaged': summary.quantity_damaged,
            'show_reclaimed': self.show_reclaimed,
            'status': status,
            'status_class': self._get_status_class(status),
        }

    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status display."""
        return {
            'in_stock': 'text-success',
            'low_stock': 'text-warning',
            'out_of_stock': 'text-danger',
            'in_transit': 'text-info',
        }.get(status, 'text-secondary')

    def _calculate_similarity(self, primary, alternative) -> float:
        """
        Calculate similarity score between two cutters.

        Args:
            primary: Primary CutterDetail
            alternative: Alternative CutterDetail

        Returns:
            Similarity score (0-1)
        """
        score = 0.0

        # Same size (most important)
        if primary.cutter_size == alternative.cutter_size:
            score += 0.5

        # Same PDC type
        if hasattr(primary, 'pdc_type') and hasattr(alternative, 'pdc_type'):
            if primary.pdc_type == alternative.pdc_type:
                score += 0.3

        # Same manufacturer
        if hasattr(primary, 'manufacturer') and hasattr(alternative, 'manufacturer'):
            if primary.manufacturer == alternative.manufacturer:
                score += 0.2

        return score

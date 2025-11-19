"""
Cutter BOM Validator Service

Real-time validation service for cutter BOM and Map entries.

Features:
- Prevent over-entry of cutter types beyond BOM limits
- Show counters for remaining quantities needed
- Validate substitutions
- Check availability against inventory
- Multi-stage validation (design, receiving, production, QC, NDT, rework, final)
"""

from typing import Dict, List, Tuple, Optional
from django.db.models import Count, Q
from decimal import Decimal


class ValidationResult:
    """
    Structured validation result with status, message, and data.
    """

    def __init__(
        self,
        is_valid: bool,
        message: str,
        data: Optional[Dict] = None,
        warnings: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.message = message
        self.data = data or {}
        self.warnings = warnings or []

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'is_valid': self.is_valid,
            'message': self.message,
            'data': self.data,
            'warnings': self.warnings,
        }


class CutterBOMValidator:
    """
    Validator for cutter BOM and Map entries.

    Provides real-time validation as users enter cutters in the grid.
    """

    def __init__(self, map_header):
        """
        Initialize validator for a specific map.

        Args:
            map_header: CutterMapHeader instance
        """
        self.map_header = map_header
        self.bom_grid = map_header.source_bom_grid

    def validate_cell_entry(
        self,
        cell,
        cutter_type,
        check_availability: bool = True
    ) -> ValidationResult:
        """
        Validate adding a cutter type to a specific cell.

        Args:
            cell: CutterMapCell instance
            cutter_type: CutterDetail instance to validate
            check_availability: Whether to check inventory availability

        Returns:
            ValidationResult with validation outcome
        """
        # Get BOM summary for this cutter type
        from floor_app.operations.inventory.models import CutterBOMSummary

        summary = CutterBOMSummary.objects.filter(
            grid_header=self.bom_grid,
            cutter_type=cutter_type
        ).first()

        # Check if cutter type is in BOM
        if not summary:
            return ValidationResult(
                is_valid=False,
                message=f"{cutter_type} is not in the BOM for this bit",
                data={
                    'cutter_type': str(cutter_type),
                    'in_bom': False,
                }
            )

        # Count current usage (excluding this cell if already has this type)
        current_count = self.map_header.cells.filter(
            actual_cutter_type=cutter_type
        ).exclude(id=cell.id).count()

        required = summary.required_quantity
        remaining_after = required - (current_count + 1)

        # Check if over limit
        if current_count >= required:
            return ValidationResult(
                is_valid=False,
                message=f"BOM limit reached: Already have {current_count}/{required} of {cutter_type}",
                data={
                    'cutter_type': str(cutter_type),
                    'required': required,
                    'current': current_count,
                    'remaining': 0,
                    'over_limit': True,
                }
            )

        # Check if this is a substitution
        is_substitution = (
            cell.required_cutter_type and
            cell.required_cutter_type != cutter_type
        )

        warnings = []
        if is_substitution:
            warnings.append(
                f"Substitution: Cell requires {cell.required_cutter_type}, "
                f"but {cutter_type} will be installed"
            )

        # Check availability if requested
        availability_data = {}
        if check_availability:
            avail_result = self._check_availability(cutter_type)
            availability_data = avail_result.data

            if not avail_result.is_valid:
                warnings.append(avail_result.message)

        # Success
        new_count = current_count + 1
        return ValidationResult(
            is_valid=True,
            message=f"OK: {new_count}/{required} used, {remaining_after} remaining",
            data={
                'cutter_type': str(cutter_type),
                'required': required,
                'current': current_count,
                'new_count': new_count,
                'remaining': remaining_after,
                'is_substitution': is_substitution,
                'availability': availability_data,
            },
            warnings=warnings
        )

    def validate_entire_map(self) -> ValidationResult:
        """
        Validate entire map against BOM.

        Returns:
            ValidationResult with complete validation summary
        """
        from floor_app.operations.inventory.models import CutterBOMSummary

        errors = []
        warnings = []
        summary_data = {}

        # Validate each cutter type in BOM
        for summary in self.bom_grid.summaries.all():
            cutter_type = summary.cutter_type
            required = summary.required_quantity

            # Count actual in map
            actual = self.map_header.cells.filter(
                actual_cutter_type=cutter_type
            ).count()

            remaining = required - actual

            summary_data[str(cutter_type)] = {
                'cutter_type_id': cutter_type.id,
                'required': required,
                'actual': actual,
                'remaining': remaining,
                'status': 'OK' if remaining == 0 else ('UNDER' if remaining > 0 else 'OVER')
            }

            if remaining > 0:
                warnings.append(
                    f"{cutter_type}: Need {remaining} more (has {actual}/{required})"
                )
            elif remaining < 0:
                errors.append(
                    f"{cutter_type}: Over-entered by {abs(remaining)} (has {actual}/{required})"
                )

        # Check for substitutions
        substitutions = self.map_header.cells.filter(
            required_cutter_type__isnull=False,
            actual_cutter_type__isnull=False
        ).exclude(
            required_cutter_type=models.F('actual_cutter_type')
        ).count()

        if substitutions > 0:
            warnings.append(f"{substitutions} cells have substitutions")

        # Check for empty required cells
        empty_required = self.map_header.cells.filter(
            required_cutter_type__isnull=False,
            actual_cutter_type__isnull=True
        ).count()

        if empty_required > 0:
            warnings.append(f"{empty_required} required cells are still empty")

        # Overall validation
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            message="Validation complete" if is_valid else f"{len(errors)} error(s) found",
            data={
                'summary': summary_data,
                'total_errors': len(errors),
                'total_warnings': len(warnings),
                'empty_required': empty_required,
                'substitutions': substitutions,
            },
            warnings=warnings + errors
        )

    def get_remaining_quantities(self) -> Dict[int, Dict]:
        """
        Get remaining quantities needed for each cutter type.

        Returns:
            Dict mapping cutter_type_id to remaining quantity info
        """
        from floor_app.operations.inventory.models import CutterBOMSummary

        remaining = {}

        for summary in self.bom_grid.summaries.all():
            cutter_type = summary.cutter_type
            required = summary.required_quantity

            # Count actual in map
            actual = self.map_header.cells.filter(
                actual_cutter_type=cutter_type
            ).count()

            remaining[cutter_type.id] = {
                'cutter_type': str(cutter_type),
                'required': required,
                'actual': actual,
                'remaining': required - actual,
                'percentage': int((actual / required * 100) if required > 0 else 0),
            }

        return remaining

    def get_cell_validation_state(self, cell) -> Dict:
        """
        Get validation state for a specific cell.

        Returns dict with validation info for UI display.
        """
        state = {
            'cell_reference': cell.cell_reference,
            'status': cell.status,
            'color': cell.color_code,
            'is_match': cell.is_match,
            'is_empty': cell.actual_cutter_type is None,
            'has_substitution': False,
            'messages': [],
        }

        # Check for substitution
        if cell.required_cutter_type and cell.actual_cutter_type:
            if cell.required_cutter_type != cell.actual_cutter_type:
                state['has_substitution'] = True
                state['messages'].append(
                    f"Substitution: Requires {cell.required_cutter_type}, "
                    f"has {cell.actual_cutter_type}"
                )

        # Get remaining count for this cutter type if populated
        if cell.actual_cutter_type:
            remaining = self.get_remaining_quantities()
            if cell.actual_cutter_type.id in remaining:
                rem_info = remaining[cell.actual_cutter_type.id]
                state['remaining_info'] = rem_info
                state['messages'].append(
                    f"{rem_info['actual']}/{rem_info['required']} used, "
                    f"{rem_info['remaining']} remaining"
                )

        return state

    def _check_availability(self, cutter_type) -> ValidationResult:
        """
        Check inventory availability for a cutter type.

        Args:
            cutter_type: CutterDetail instance

        Returns:
            ValidationResult with availability info
        """
        from floor_app.operations.inventory.models import CutterInventorySummary

        summary = CutterInventorySummary.objects.filter(
            cutter_detail=cutter_type
        ).first()

        if not summary:
            return ValidationResult(
                is_valid=False,
                message=f"No inventory summary found for {cutter_type}",
                data={
                    'available': 0,
                    'has_inventory': False,
                }
            )

        # Calculate available based on reclaimed filter
        show_reclaimed = self.bom_grid.show_reclaimed_cutters

        if show_reclaimed:
            total_available = summary.quantity_new_good + summary.quantity_reclaimed_good
        else:
            total_available = summary.quantity_new_good

        is_available = total_available > 0

        return ValidationResult(
            is_valid=is_available,
            message=f"Available: {total_available}" if is_available else "Out of stock",
            data={
                'available_new': summary.quantity_new_good,
                'available_reclaimed': summary.quantity_reclaimed_good,
                'total_available': total_available,
                'in_transit': summary.quantity_in_transit,
                'reserved': summary.quantity_reserved,
                'damaged': summary.quantity_damaged,
                'show_reclaimed': show_reclaimed,
                'has_inventory': True,
            }
        )


# Import models at end to avoid circular imports
from django.db import models

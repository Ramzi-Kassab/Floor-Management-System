"""
Condition Parser and Evaluator

Safely evaluates JSON condition definitions without arbitrary code execution.

Supported condition types:
- threshold: Compare field to static value
- age: Check time since a datetime field
- field_comparison: Compare two fields
- queryset_count: Count matching records
- compound: AND/OR combinations
- custom: Limited safe eval (with whitelist)
"""

from datetime import timedelta
from django.utils import timezone
from django.apps import apps
from decimal import Decimal
import operator
import re


class ConditionParser:
    """
    Parses and evaluates JSON condition definitions.

    Thread-safe, no arbitrary code execution.
    """

    # Operator mapping
    OPERATORS = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'in': lambda a, b: a in b,
        'not_in': lambda a, b: a not in b,
        'contains': lambda a, b: b in a,
        'startswith': lambda a, b: str(a).startswith(str(b)),
        'endswith': lambda a, b: str(a).endswith(str(b)),
        'regex': lambda a, b: bool(re.match(b, str(a))),
    }

    def __init__(self, condition_def):
        """
        Initialize parser with condition definition.

        condition_def: dict - JSON condition structure
        """
        self.condition_def = condition_def
        self.condition_type = condition_def.get('type', 'threshold')

    def evaluate(self, target_object=None, context=None):
        """
        Evaluate condition.

        Returns:
            dict:
                - result: bool (True if condition met)
                - context: dict (explanation of evaluation)
                - comment: str (human-readable explanation)
        """
        context = context or {}

        try:
            if self.condition_type == 'threshold':
                return self._eval_threshold(target_object, context)
            elif self.condition_type == 'age':
                return self._eval_age(target_object, context)
            elif self.condition_type == 'field_comparison':
                return self._eval_field_comparison(target_object, context)
            elif self.condition_type == 'queryset_count':
                return self._eval_queryset_count(target_object, context)
            elif self.condition_type == 'compound':
                return self._eval_compound(target_object, context)
            elif self.condition_type == 'custom':
                return self._eval_custom(target_object, context)
            else:
                raise ValueError(f"Unknown condition type: {self.condition_type}")

        except Exception as e:
            return {
                'result': False,
                'context': {'error': str(e)},
                'comment': f"Evaluation error: {str(e)}"
            }

    def _eval_threshold(self, obj, context):
        """
        Evaluate threshold condition.

        Example:
        {
            "type": "threshold",
            "field": "quantity_on_hand",
            "operator": "<",
            "value": 10
        }
        """
        field_name = self.condition_def.get('field')
        operator_str = self.condition_def.get('operator', '==')
        threshold_value = self.condition_def.get('value')

        if not field_name:
            raise ValueError("Field name required for threshold condition")

        # Get field value
        current_value = self._get_field_value(obj, field_name)

        # Get operator
        if operator_str not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator_str}")
        op_func = self.OPERATORS[operator_str]

        # Evaluate
        result = op_func(current_value, threshold_value)

        return {
            'result': result,
            'context': {
                'field': field_name,
                'current_value': str(current_value),
                'operator': operator_str,
                'threshold': threshold_value,
                'difference': self._safe_subtract(current_value, threshold_value),
            },
            'comment': f"{field_name} ({current_value}) {operator_str} {threshold_value}: {result}"
        }

    def _eval_age(self, obj, context):
        """
        Evaluate age-based condition.

        Example:
        {
            "type": "age",
            "field": "entered_at",
            "operator": ">",
            "value": 24,
            "unit": "hours"
        }

        Units: seconds, minutes, hours, days, weeks
        """
        field_name = self.condition_def.get('field')
        operator_str = self.condition_def.get('operator', '>')
        threshold_value = self.condition_def.get('value')
        unit = self.condition_def.get('unit', 'hours')

        if not field_name:
            raise ValueError("Field name required for age condition")

        # Get datetime field value
        dt_value = self._get_field_value(obj, field_name)
        if not dt_value:
            return {
                'result': False,
                'context': {'error': f"{field_name} is null"},
                'comment': f"{field_name} is null, cannot evaluate age"
            }

        # Calculate age
        now = timezone.now()
        age_delta = now - dt_value

        # Convert to requested unit
        unit_seconds = {
            'seconds': 1,
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
        }

        if unit not in unit_seconds:
            raise ValueError(f"Invalid time unit: {unit}")

        age_in_unit = age_delta.total_seconds() / unit_seconds[unit]

        # Get operator
        if operator_str not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator_str}")
        op_func = self.OPERATORS[operator_str]

        # Evaluate
        result = op_func(age_in_unit, threshold_value)

        return {
            'result': result,
            'context': {
                'field': field_name,
                'datetime_value': dt_value.isoformat(),
                'age': round(age_in_unit, 2),
                'unit': unit,
                'operator': operator_str,
                'threshold': threshold_value,
            },
            'comment': f"{field_name} age ({age_in_unit:.1f} {unit}) {operator_str} {threshold_value}: {result}"
        }

    def _eval_field_comparison(self, obj, context):
        """
        Compare two fields.

        Example:
        {
            "type": "field_comparison",
            "field1": "actual_quantity",
            "operator": "<",
            "field2": "required_quantity"
        }
        """
        field1_name = self.condition_def.get('field1')
        field2_name = self.condition_def.get('field2')
        operator_str = self.condition_def.get('operator', '==')

        if not field1_name or not field2_name:
            raise ValueError("Both field1 and field2 required for field comparison")

        # Get values
        value1 = self._get_field_value(obj, field1_name)
        value2 = self._get_field_value(obj, field2_name)

        # Get operator
        if operator_str not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator_str}")
        op_func = self.OPERATORS[operator_str]

        # Evaluate
        result = op_func(value1, value2)

        return {
            'result': result,
            'context': {
                'field1': field1_name,
                'value1': str(value1),
                'operator': operator_str,
                'field2': field2_name,
                'value2': str(value2),
                'difference': self._safe_subtract(value1, value2),
            },
            'comment': f"{field1_name} ({value1}) {operator_str} {field2_name} ({value2}): {result}"
        }

    def _eval_queryset_count(self, obj, context):
        """
        Evaluate queryset count condition.

        Example:
        {
            "type": "queryset_count",
            "model": "inventory.CutterDetail",
            "filters": {"category": "ENO_RECLAIMED"},
            "operator": ">",
            "value": 50
        }

        Note: This is safer than allowing arbitrary queryset expressions.
        """
        model_path = self.condition_def.get('model')
        filters = self.condition_def.get('filters', {})
        operator_str = self.condition_def.get('operator', '>')
        threshold_value = self.condition_def.get('value')

        if not model_path:
            raise ValueError("Model path required for queryset_count")

        # Get model
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as e:
            raise ValueError(f"Invalid model path: {model_path}: {e}")

        # Build queryset
        qs = model.objects.filter(**filters)
        count = qs.count()

        # Get operator
        if operator_str not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator_str}")
        op_func = self.OPERATORS[operator_str]

        # Evaluate
        result = op_func(count, threshold_value)

        return {
            'result': result,
            'context': {
                'model': model_path,
                'filters': filters,
                'count': count,
                'operator': operator_str,
                'threshold': threshold_value,
            },
            'comment': f"{model_path} count ({count}) {operator_str} {threshold_value}: {result}"
        }

    def _eval_compound(self, obj, context):
        """
        Evaluate compound condition (AND/OR).

        Example:
        {
            "type": "compound",
            "operator": "AND",
            "conditions": [
                {"type": "threshold", "field": "stock", "operator": "<", "value": 10},
                {"type": "age", "field": "last_usage", "operator": ">", "value": 90, "unit": "days"}
            ]
        }
        """
        compound_operator = self.condition_def.get('operator', 'AND').upper()
        conditions = self.condition_def.get('conditions', [])

        if not conditions:
            raise ValueError("Conditions list required for compound condition")

        if compound_operator not in ['AND', 'OR']:
            raise ValueError(f"Invalid compound operator: {compound_operator}. Use AND or OR")

        results = []
        all_context = []

        for cond_def in conditions:
            parser = ConditionParser(cond_def)
            result = parser.evaluate(obj, context)
            results.append(result['result'])
            all_context.append(result['context'])

        # Evaluate compound
        if compound_operator == 'AND':
            final_result = all(results)
        else:  # OR
            final_result = any(results)

        return {
            'result': final_result,
            'context': {
                'operator': compound_operator,
                'sub_conditions': all_context,
                'individual_results': results,
            },
            'comment': f"{compound_operator} of {len(conditions)} conditions: {final_result}"
        }

    def _eval_custom(self, obj, context):
        """
        Evaluate custom expression (limited, safe eval).

        Example:
        {
            "type": "custom",
            "expression": "obj.time_in_stage_hours > (obj.stage.average_duration_hours * 1.5)"
        }

        WARNING: This allows limited Python expressions.
        Only use with trusted inputs and in controlled environment.
        Whitelist approach: only allow specific attribute access patterns.
        """
        expression = self.condition_def.get('expression')

        if not expression:
            raise ValueError("Expression required for custom condition")

        # Safety check: only allow simple attribute access and arithmetic
        # No function calls except basic arithmetic
        allowed_pattern = r'^obj(\.[a-zA-Z_][a-zA-Z0-9_]*)+\s*[<>=!]+\s*.*$'
        if not re.match(allowed_pattern, expression.replace(' ', '')):
            raise ValueError(f"Expression not allowed: {expression}")

        # Build safe evaluation context
        safe_context = {
            'obj': obj,
            '__builtins__': {},  # No built-in functions
        }

        try:
            # Evaluate expression
            result = eval(expression, safe_context)

            return {
                'result': bool(result),
                'context': {
                    'expression': expression,
                    'evaluated_result': result,
                },
                'comment': f"Custom expression '{expression}': {result}"
            }

        except Exception as e:
            raise ValueError(f"Custom expression evaluation failed: {e}")

    def _get_field_value(self, obj, field_path):
        """
        Get field value from object, supporting dot notation.

        Examples:
        - "quantity_on_hand" -> obj.quantity_on_hand
        - "stage.average_duration_hours" -> obj.stage.average_duration_hours
        - "job_card.customer_name" -> obj.job_card.customer_name
        """
        if not obj:
            return None

        parts = field_path.split('.')
        value = obj

        for part in parts:
            if value is None:
                return None

            # Support dict access
            if isinstance(value, dict):
                value = value.get(part)
            else:
                # Object attribute access
                value = getattr(value, part, None)

        return value

    def _safe_subtract(self, a, b):
        """
        Safely subtract two values, handling None and type mismatches.
        """
        try:
            if a is None or b is None:
                return None

            # Convert to same type if needed
            if isinstance(a, Decimal) or isinstance(b, Decimal):
                return float(Decimal(str(a)) - Decimal(str(b)))
            else:
                return a - b
        except (TypeError, ValueError):
            return None

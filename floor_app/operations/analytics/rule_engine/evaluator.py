"""
Rule Evaluator

Coordinates rule execution:
1. Parse condition definition
2. Evaluate condition
3. Record result
4. Trigger action if needed
"""

from django.apps import apps
from .conditions import ConditionParser
import time


class RuleEvaluator:
    """
    Evaluates an AutomationRule.

    Handles:
    - Condition parsing and evaluation
    - Target object resolution
    - Result logging
    - Performance tracking
    """

    def __init__(self, rule):
        """
        Initialize evaluator with a rule.

        rule: AutomationRule instance
        """
        self.rule = rule

    def evaluate(self, target_object=None, context=None):
        """
        Evaluate the rule.

        Args:
            target_object: Optional specific object to evaluate against
            context: Optional additional context dict

        Returns:
            dict:
                - triggered: bool
                - context: dict (evaluation details)
                - comment: str (explanation)
                - duration_ms: int (execution time)
        """
        start_time = time.time()

        context = context or {}

        try:
            # Get target objects if not provided
            if target_object is None:
                target_objects = self._get_target_objects()
            else:
                target_objects = [target_object]

            # If no target objects, evaluate as global rule
            if not target_objects:
                result = self._evaluate_single(None, context)
            else:
                # Evaluate for each target object
                # For now, trigger if ANY object matches
                # TODO: Add option for ALL vs ANY
                triggered_objects = []
                all_contexts = []

                for obj in target_objects:
                    result = self._evaluate_single(obj, context)
                    if result['result']:
                        triggered_objects.append({
                            'object': obj,
                            'context': result['context']
                        })
                    all_contexts.append(result['context'])

                # Final result
                result = {
                    'result': len(triggered_objects) > 0,
                    'context': {
                        'triggered_count': len(triggered_objects),
                        'total_evaluated': len(target_objects),
                        'triggered_objects': [
                            {
                                'object_id': getattr(t['object'], 'id', None),
                                'object_str': str(t['object']),
                                'context': t['context']
                            }
                            for t in triggered_objects[:10]  # Limit to 10 for JSON size
                        ],
                    },
                    'comment': f"Triggered for {len(triggered_objects)} of {len(target_objects)} objects"
                }

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'triggered': result['result'],
                'context': result['context'],
                'comment': result.get('comment', ''),
                'duration_ms': duration_ms,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            raise

    def _evaluate_single(self, target_object, context):
        """Evaluate rule for a single target object."""
        parser = ConditionParser(self.rule.condition_definition)
        return parser.evaluate(target_object=target_object, context=context)

    def _get_target_objects(self):
        """
        Get target objects based on rule configuration.

        Returns queryset or list of objects to evaluate.
        """
        if not self.rule.target_model:
            # No specific target model - global rule
            return []

        try:
            # Parse model path
            app_label, model_name = self.rule.target_model.split('.')
            model = apps.get_model(app_label, model_name)

            # Get all objects (can be customized with filters)
            # TODO: Add filter configuration to rule
            qs = model.objects.all()

            # Limit to reasonable number for performance
            # Can make this configurable per rule
            return list(qs[:1000])

        except (ValueError, LookupError) as e:
            raise ValueError(f"Invalid target model: {self.rule.target_model}: {e}")

    @classmethod
    def evaluate_all_active_rules(cls, rule_scope=None):
        """
        Evaluate all active rules.

        Args:
            rule_scope: Optional filter by scope

        Returns:
            dict with results summary
        """
        from floor_app.operations.analytics.models import AutomationRule

        # Get rules to evaluate
        rules = AutomationRule.objects.filter(is_active=True, is_approved=True)

        if rule_scope:
            rules = rules.filter(rule_scope=rule_scope)

        # Filter by trigger mode (only scheduled for this method)
        rules = rules.filter(trigger_mode='SCHEDULED')

        results = {
            'total_evaluated': 0,
            'total_triggered': 0,
            'total_errors': 0,
            'rule_results': [],
        }

        for rule in rules:
            try:
                execution = rule.execute()

                results['total_evaluated'] += 1
                if execution.was_triggered:
                    results['total_triggered'] += 1

                results['rule_results'].append({
                    'rule_code': rule.rule_code,
                    'triggered': execution.was_triggered,
                    'comment': execution.comment,
                })

            except Exception as e:
                results['total_errors'] += 1
                results['rule_results'].append({
                    'rule_code': rule.rule_code,
                    'error': str(e),
                })

        return results

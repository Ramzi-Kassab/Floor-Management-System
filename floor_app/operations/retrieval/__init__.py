"""
Retrieval/Undo System for Floor Management System

Allows employees to undo mistakes within a time window with supervisor approval.
Tracks all retrievals for employee accuracy metrics and audit trails.

Features:
- Auto-approval within 15-minute time window
- Supervisor notifications and manual approval
- Dependency checking (prevents retrieval if dependent processes exist)
- Full audit trail of original data
- Employee accuracy metrics tracking
- Generic retrieval capability via RetrievableMixin

Usage:
    # In your model
    from floor_app.operations.retrieval.mixins import RetrievableMixin

    class MyModel(RetrievableMixin, models.Model):
        # your fields here
        pass

    # Create retrieval request
    obj = MyModel.objects.get(pk=1)
    request = obj.create_retrieval_request(
        employee=request.user,
        reason="Made a mistake in data entry",
        action_type='DELETE'
    )

    # Check if can be retrieved
    can_retrieve, reasons = obj.can_be_retrieved()

    # Perform retrieval (after approval)
    if request.is_approved:
        obj.perform_retrieval(request)
"""

default_app_config = 'floor_app.operations.retrieval.apps.RetrievalConfig'

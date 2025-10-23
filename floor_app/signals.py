# floor_app/signals.py
from __future__ import annotations

import decimal
import uuid
from datetime import date, datetime
from typing import Any, Dict, Iterable

from django.db import transaction
from django.db.models import Model
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.contenttypes.models import ContentType

from .middleware import get_current_request
from .utils import get_client_ip
from .models import AuditLog, AuditMixin, Employee, Contact


# ---------- Helpers ----------

def _serialize(val: Any) -> Any:
    """JSON-safe, readable values for AuditLog JSON fields."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return str(val)  # keep precision
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, Model):
        return str(val) or f"{val._meta.label}:{val.pk}"
    return str(val)


def _concrete_field_names(instance: Model) -> Iterable[str]:
    """Only concrete DB fields (skip M2M/related managers) for speed/clarity."""
    return [f.name for f in instance._meta.concrete_fields]


def _build_values_dict(instance: Model, exclude: Iterable[str]) -> Dict[str, Any]:
    """Build a JSON-serializable dict of field values for auditing."""
    fields = [f for f in _concrete_field_names(instance) if f not in exclude]
    raw = model_to_dict(instance, fields=fields)
    return {k: _serialize(v) for k, v in raw.items()}


# ---------- Audit Signals ----------

@receiver(pre_save, dispatch_uid="audit_pre_save_v1")
def _capture_before(sender, instance, **kwargs):
    """
    - Stash a pre-save snapshot for diffs.
    - Auto-fill created_by / updated_by from the current request user.
    """
    if not hasattr(sender, "_meta"):
        return
    if getattr(sender._meta, "proxy", False):
        return
    if getattr(sender._meta, "managed", True) is False:
        return
    if sender is AuditLog:
        return
    if not isinstance(instance, AuditMixin):
        return

    # Snapshot existing row (for diffs)
    if instance.pk:
        try:
            previous = sender.objects.get(pk=instance.pk)
            instance.__pre = model_to_dict(previous, fields=_concrete_field_names(previous))
        except sender.DoesNotExist:
            instance.__pre = None
    else:
        instance.__pre = None

    # Auto-fill who
    req = get_current_request()
    user = getattr(req, "user", None)
    if user and getattr(user, "is_authenticated", False):
        if instance.pk is None and hasattr(instance, "created_by_id") and instance.created_by_id is None:
            instance.created_by = user
        if hasattr(instance, "updated_by_id"):
            instance.updated_by = user


@receiver(post_save, dispatch_uid="audit_post_save_v1")
def _log_after(sender, instance, created, **kwargs):
    """After commit, write an AuditLog entry with old/new values."""
    if not hasattr(sender, "_meta"):
        return
    if getattr(sender._meta, "proxy", False):
        return
    if getattr(sender._meta, "managed", True) is False:
        return
    if sender is AuditLog:
        return
    if not isinstance(instance, AuditMixin):
        return

    exclude = set(getattr(instance, "audit_exclude", ())) | {"created_at", "updated_at", "created_by", "updated_by"}
    new_values = _build_values_dict(instance, exclude)

    old_values = None
    if not created and getattr(instance, "__pre", None) is not None:
        old_values = {k: _serialize(v) for k, v in instance.__pre.items() if k not in exclude}

    req = get_current_request()
    ua = req.META.get("HTTP_USER_AGENT") if req else None
    ip = get_client_ip(req)
    user = getattr(req, "user", None) if req else None
    actor = user if (user and getattr(user, "is_authenticated", False)) else None

    transaction.on_commit(lambda: AuditLog.objects.create(
        timestamp=timezone.now(),
        user=actor,
        table_name=sender._meta.db_table,
        record_id=instance.pk,
        action="create" if created else "update",
        old_values=None if created else old_values,
        new_values=new_values,
        ip_address=ip,
        user_agent=ua,
    ))

    if hasattr(instance, "__pre"):
        try:
            delattr(instance, "__pre")
        except Exception:
            pass


@receiver(post_delete, dispatch_uid="audit_post_delete_v1")
def _log_delete(sender, instance, **kwargs):
    """Log deletes with minimal payload."""
    if not hasattr(sender, "_meta"):
        return
    if getattr(sender._meta, "proxy", False):
        return
    if getattr(sender._meta, "managed", True) is False:
        return
    if sender is AuditLog:
        return
    if not isinstance(instance, AuditMixin):
        return

    req = get_current_request()
    ua = req.META.get("HTTP_USER_AGENT") if req else None
    ip = get_client_ip(req)
    user = getattr(req, "user", None) if req else None
    actor = user if (user and getattr(user, "is_authenticated", False)) else None

    payload = {"pk": _serialize(getattr(instance, "pk", None))}

    transaction.on_commit(lambda: AuditLog.objects.create(
        timestamp=timezone.now(),
        user=actor,
        table_name=sender._meta.db_table,
        record_id=getattr(instance, "pk", None) or 0,
        action="delete",
        old_values=payload,
        new_values=None,
        ip_address=ip,
        user_agent=ua,
    ))


# ---------- Employee auto-user + group sync ----------

def _unique_username(base: str) -> str:
    """Ensure username uniqueness by suffixing a counter if needed."""
    User = get_user_model()
    base = (base or "user").lower().replace(" ", "")
    allowed = "".join(ch for ch in base if ch.isalnum() or ch in "._-")
    base = allowed or "user"
    candidate = base
    i = 1
    while User.objects.filter(username=candidate).exists():
        i += 1
        candidate = f"{base}{i}"
    return candidate


def _primary_contact_email_for_party(instance) -> str | None:
    """
    Return the primary contact's primary email for the given model instance.
    Looks up Contact where party=(instance) and then its ContactMethod(kind='email').
    """
    if not instance.pk:
        return None
    ct = ContentType.objects.get_for_model(instance.__class__)
    primary = Contact.objects.filter(party_type=ct, party_id=instance.pk, is_primary=True).first()
    if not primary:
        return None
    m = primary.methods.filter(kind='email', is_primary=True).first() or primary.methods.filter(kind='email').first()
    return (m.email if m else None)


@receiver(post_save, sender=Employee, dispatch_uid="employee_autouser_v2")
def ensure_user_for_employee(sender, instance: Employee, created, **kwargs):
    """
    On first create: create a Django user if missing.
    On create & update: sync Employee.auth_group to the user.
    Uses Employee.email; if empty, falls back to primary contact's primary email.
    """
    User = get_user_model()

    def _create_user_and_attach():
        # Username: 'e' + employee_code (lowercased) -> unique
        if instance.employee_code:
            base_username = f"e{instance.employee_code.lower()}"
        else:
            first = (instance.first_name or "").strip().lower()
            last  = (instance.last_name  or "").strip().lower()
            base_username = f"{first}.{last}" if (first or last) else "employee"

        username = _unique_username(base_username)

        # Email: prefer Employee.email, else primary contact email
        email = (instance.email or "").strip()
        if not email:
            email = _primary_contact_email_for_party(instance) or ""

        temp_password = get_random_string(12)  # in prod, send set-password link instead

        user = User.objects.create_user(
            username=username,
            email=email,
            password=temp_password,
            first_name=instance.first_name or "",
            last_name=instance.last_name or "",
            is_active=True,
            is_staff=bool(instance.allow_admin_login),
        )

        instance.user = user
        instance.save(update_fields=["user"])

    # Create user once, after the employee row is committed
    if not instance.user_id:
        transaction.on_commit(_create_user_and_attach)

    # Sync selected group to the user (on both create & update)
    def _sync_group():
        if instance.user_id:
            # Keep group sync as-is:
            if getattr(instance, "auth_group", None):
                instance.user.groups.set([instance.auth_group])
            else:
                instance.user.groups.clear()

            # <-- CHANGE: keep is_staff in sync with the checkbox (independent of group)
            instance.user.is_staff = bool(instance.allow_admin_login and instance.auth_group)
            instance.user.save(update_fields=["is_staff"])

    transaction.on_commit(_sync_group)

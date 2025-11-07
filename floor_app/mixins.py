import uuid
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# ---------- Soft delete ----------
class SoftDeleteQuerySet(models.QuerySet):
    def alive(self): return self.filter(is_deleted=False)
    def deleted(self): return self.filter(is_deleted=True)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    # Default: only alive records
    objects = SoftDeleteManager()
    # Opt-in: include deleted as well
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=['is_deleted', 'deleted_at'])


# ---------- Public ID ----------

class PublicIdMixin(models.Model):
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    class Meta:
        abstract = True



# ---------- Document reference ----------
class DocumentReferenceMixin(models.Model):
    """Mixin for models that reference other documents"""
    ref_doctype = models.CharField(max_length=32, blank=True, db_index=True)
    ref_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['ref_doctype', 'ref_id'], name='ix_%(class)s_ref'),
        ]


# ---------- Party type & reference ----------
class PartyType(models.TextChoices):
    CUSTOMER = 'Customer', 'Customer'
    SUPPLIER = 'Supplier', 'Supplier'

# mixins.py


class PartyReferenceMixin(models.Model):
    party_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, blank=True,                         # <-- make TEMPORARILY nullable
        related_name="%(app_label)s_%(class)s_party_ct",
    )
    party_object_id = models.BigIntegerField(null=True, blank=True)  # <-- TEMP nullable
    party = GenericForeignKey("party_content_type", "party_object_id")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["party_content_type", "party_object_id"], name="ix_%(class)s_party"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(party_object_id__gt=0), name="ck_%(class)s_party_id_pos"),
        ]

    # Optional convenience
    def set_party(self, obj):
        self.party_content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        self.party_object_id = obj.pk

    @property
    def party_label(self):
        return f"{self.party_content_type.app_label}.{self.party_content_type.model}:{self.party_object_id}"



# ---------- Posting ----------
class PostingMixin(models.Model):
    """Mixin for documents with posting timestamp"""
    posting_ts = models.DateTimeField(db_index=True, default=timezone.now)

    class Meta:
        abstract = True
        ordering = ['-posting_ts']


class GenericPartyReferenceMixin(models.Model):
    """
    Generic link to *any* owner model (Employee, Customer, Supplier, Carrier, Company, ...).
    This is what lets us add contacts on those owner admin pages.
    """
    party_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, db_index=True)
    party_id   = models.BigIntegerField(db_index=True)
    party      = GenericForeignKey('party_type', 'party_id')

    class Meta:
        abstract = True
        indexes = [models.Index(fields=['party_type', 'party_id'], name='ix_%(class)s_party_ct')]
        constraints = [
            models.CheckConstraint(check=models.Q(party_id__gt=0), name='ck_%(class)s_party_id_pos'),
        ]

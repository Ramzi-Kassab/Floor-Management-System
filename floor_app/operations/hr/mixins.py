from django.conf import settings
from django.db import models
from django.utils import timezone

class HRAuditMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_hr_created"
    )
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_hr_updated"
    )
    remarks = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        abstract = True



# Soft delete aligned with your existing approach (hidden by default manager)
class HRSoftDeleteQuerySet(models.QuerySet):
    def alive(self): return self.filter(is_deleted=False)
    def deleted(self): return self.filter(is_deleted=True)

class HRSoftDeleteManager(models.Manager):
    def get_queryset(self):
        return HRSoftDeleteQuerySet(self.model, using=self._db).alive()

class HRAllObjectsManager(models.Manager):
    def get_queryset(self):
        return HRSoftDeleteQuerySet(self.model, using=self._db)

class HRSoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    # default manager hides deleted rows
    objects = HRSoftDeleteManager()
    # opt-in manager exposes all rows
    all_objects = HRAllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=["is_deleted", "deleted_at"])


class HREffectiveDatedMixin(models.Model):
    effective_start = models.DateField()
    effective_end = models.DateField(null=True, blank=True)  # open-ended when null

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.effective_end and self.effective_end < self.effective_start:
            from django.core.exceptions import ValidationError
            raise ValidationError("effective_end cannot be earlier than effective_start")

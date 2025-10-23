from django.db import models


class BaseQuerySet(models.QuerySet):
    def active(self):
        fields = {f.name for f in self.model._meta.fields}
        if 'is_active' in fields:
            return self.filter(is_active=True)
        if 'status' in fields:
            return self.exclude(status__in=['Cancelled', 'Inactive', 'Retired'])
        return self

    def for_company(self, company):
        return self.filter(company=company) if 'company' in {f.name for f in self.model._meta.fields} else self


class BaseManager(models.Manager):
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)

    def active(self): return self.get_queryset().active()

    def for_company(self, company): return self.get_queryset().for_company(company)

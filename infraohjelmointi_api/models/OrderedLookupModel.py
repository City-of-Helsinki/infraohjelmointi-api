from django.db import models
from django.db.models import Max


class OrderedLookupModel(models.Model):
    order = models.IntegerField(null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self._state.adding and self.order is None:
            max_order = self.__class__.objects.aggregate(Max("order"))["order__max"]
            self.order = (max_order + 1) if max_order is not None else 0
        super().save(*args, **kwargs)
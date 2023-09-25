from django.db import models
from simple_history.models import HistoricalRecords
from overrides import override
from django.db.models import UUIDField
import uuid
from .User import User

import logging


class HistoricalModel(models.Model):
    class Meta:
        abstract = True

    history = HistoricalRecords(
        inherit=True,
        user_model=User,
        history_user_id_field=UUIDField(default=uuid.uuid4, null=True),
    )

    @override
    def save(self, *args, **kwargs):
        # we need previous content to store to history
        old_instance = (
            self.__class__.objects.get(id=self.id) if self.createdDate != None else None
        )

        super().save(*args, **kwargs)
        if old_instance == None:
            self.history.filter().delete()
        # store the old content to history
        else:
            history_obj = self.history.latest()
            for field in self.history_fields:
                field_value = getattr(old_instance, field)
                setattr(history_obj, field, field_value)

            # history user must be defined but for any reason let set it as None if not nefined
            history_user = getattr(old_instance, "_history_user", None)
            # history user must be defined
            if history_user != None:
                setattr(history_obj, "history_user", history_user)

            history_obj.save()

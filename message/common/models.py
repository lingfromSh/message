# Third Party Library
from message.common.fields import ULIDField
from pydantic import ConfigDict
from tortoise import Model
from tortoise import fields
from tortoise.manager import Manager
from tortoise.queryset import QuerySet
from tortoise.timezone import now

__all__ = [
    "ActiveObjectsManager",
    "BaseModel",
]


class ActiveObjectsManager(Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_deleted=False, deleted_at__isnull=True)


class BaseModel(Model):
    id = ULIDField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)

    active_objects = ActiveObjectsManager()

    class Meta:
        abstract = True

    class PydanticMeta:
        exclude = ("is_deleted", "deleted_at")
        model_config = ConfigDict(arbitrary_types_allowed=True)

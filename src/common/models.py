# Third Party Library
from tortoise import Model
from tortoise import fields
from tortoise.manager import Manager
from tortoise.queryset import QuerySet

# First Library
from common.fields import ULIDField

__all__ = [
    "BaseManager",
    "BaseModel",
]


class BaseManager(Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_deleted=False, deleted_at__isnull=True)


class BaseModel(Model):
    id = ULIDField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        abstract = True
        manager = BaseManager()

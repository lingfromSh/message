# Third Party Library
from tortoise import fields

# First Library
import mixins
from common.models import BaseModel


class User(mixins.UserMixin, BaseModel):
    external_id = fields.CharField(max_length=255, unique=True)
    metadata = fields.JSONField(default=dict)
    # TODO: make endpoints as many(endpoint) to one(user)
    endpoints = fields.ManyToManyField(
        "models.Contact",
        related_name="endpoints",
        through="models.Endpoint",
    )
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"

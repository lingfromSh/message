# Third Party Library
from tortoise import fields

# First Library
import mixins
from common.models import BaseModel


class User(mixins.UserMixin, BaseModel):
    external_id = fields.CharField(max_length=255, unique=True)
    metadata = fields.JSONField(default=dict)
    # TODO: make endpoints as many(endpoint) to one(user)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"

    class PydanticMeta(BaseModel.PydanticMeta):
        exclude = ("endpointss", "messages") + BaseModel.PydanticMeta.exclude


class UserEndpoint(BaseModel):
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        related_name="endpoints",
    )
    contact = fields.ForeignKeyField(
        "models.Contact",
        on_delete=fields.CASCADE,
        related_name="user_endpoints",
    )
    value = fields.JSONField(default=dict)

    class Meta:
        table = "user_endpoints"

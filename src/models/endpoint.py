# Third Party Library
from tortoise import fields

# First Library
import mixins
from common.models import BaseModel


class Endpoint(mixins.EndpointMixin, BaseModel):
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
    )
    contact = fields.ForeignKeyField(
        "models.Contact",
        on_delete=fields.CASCADE,
    )
    value = fields.JSONField(default=dict)

    class Meta:
        table = "endpoints"

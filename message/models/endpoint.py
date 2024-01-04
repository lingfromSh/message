# Third Party Library
from message import mixins
from message.common.models import BaseModel
from tortoise import fields


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

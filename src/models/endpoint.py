# Third Party Library
from tortoise import fields

# First Library
from common.models import BaseModel


class Endpoint(BaseModel):
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
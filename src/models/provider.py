# Third Party Library
from tortoise import fields

# First Library
from common.models import BaseModel


class Provider(BaseModel):
    name = fields.CharField(max_length=255)
    code = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    params = fields.JSONField(default=dict)

    contacts = fields.ForeignKeyField(
        "models.Contact",
        related_name="providers",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "providers"
        unique_together = ("code", "deleted_at")

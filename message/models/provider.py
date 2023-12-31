# Third Party Library
from message import mixins
from message.common.models import BaseModel
from tortoise import fields


class Provider(mixins.ProviderMixin, BaseModel):
    name = fields.CharField(max_length=255)
    code = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    params = fields.JSONField(default=dict)

    contacts = fields.ManyToManyField(
        "models.Contact",
        related_name="providers",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "providers"
        unique_together = ("code", "deleted_at")

# Third Party Library
from tortoise import fields

# First Library
from common.constants import MessageStatusEnum
from common.models import BaseModel


class Message(BaseModel):
    provider = fields.ForeignKeyField("models.Provider", on_delete=fields.NO_ACTION)
    end_users = fields.ManyToManyField(
        "models.User",
        related_name="messages",
    )
    endpoints = fields.ManyToManyField(
        "models.Endpoint",
        related_name="messages",
    )
    contacts = fields.JSONField(null=True)
    content = fields.JSONField(default=dict)
    status = fields.CharEnumField(
        MessageStatusEnum,
        default=MessageStatusEnum.SCHEDULED,
    )

    class Meta:
        table = "messages"

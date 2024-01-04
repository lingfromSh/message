# Third Party Library
from tortoise import fields

# First Library
import mixins
from common.constants import MessageStatusEnum
from common.models import BaseModel


class Message(mixins.MessageMixin, BaseModel):
    provider = fields.ForeignKeyField("models.Provider", on_delete=fields.NO_ACTION)
    end_users = fields.ManyToManyField(
        "models.User",
        related_name="messages",
    )
    endpoints = fields.ManyToManyField(
        "models.Endpoint",
        related_name="messages",
        on_delete=fields.NO_ACTION,
    )
    contacts = fields.JSONField(null=True)
    content = fields.TextField(null=True)
    status = fields.CharEnumField(
        MessageStatusEnum,
        default=MessageStatusEnum.PENDING,
    )
    status_history = fields.JSONField(default=list)

    class Meta:
        table = "messages"

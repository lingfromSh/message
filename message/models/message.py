# Third Party Library
from message import mixins
from message.common.constants import MessageStatusEnum
from message.common.models import BaseModel
from tortoise import fields


class Message(mixins.MessageMixin, BaseModel):
    """
    Message model represents a message history including content, status, and related users, endpoints and contacts.
    """

    provider = fields.ForeignKeyField("models.Provider", on_delete=fields.NO_ACTION)
    users = fields.ManyToManyField(
        "models.User",
        related_name="messages",
    )
    endpoints = fields.ManyToManyField(
        "models.Endpoint",
        related_name="messages",
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

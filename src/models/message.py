# Third Party Library
from tortoise import fields

# First Library
from common.models import BaseModel


class Message(BaseModel):
    provider = fields.ForeignKeyField("models.Provider", on_delete=fields.NO_ACTION)
    end_users = fields.ManyToManyField("models.User", related_name="messages")
    content = fields.JSONField(default=dict)

    class Meta:
        table = "messages"

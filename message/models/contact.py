# Third Party Library
from message import mixins
from message.common.models import BaseModel
from tortoise import fields


class Contact(mixins.ContactMixin, BaseModel):
    """
    contact is a method of notification.

    like mobile, email, slack, etc.
    """

    name = fields.CharField(max_length=255)
    code = fields.CharField(max_length=255)
    description = fields.TextField()
    definition = fields.JSONField(default=dict)

    class Meta:
        table = "contacts"
        unqiue_together = ("code", "deleted_at")

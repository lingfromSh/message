# Third Party Library
from message import mixins
from message.common.models import BaseModel
from tortoise import fields


class Contact(mixins.ContactMixin, BaseModel):
    """
    Contact is a method of notification

    like mobile, email, slack, etc.
    """

    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    code = fields.CharField(max_length=255)
    definition = fields.JSONField(default=dict)
    # builtin contact can not be deleted
    is_builtin = fields.BooleanField(default=False)

    class Meta:
        table = "contacts"
        unqiue_together = ("code", "deleted_at")

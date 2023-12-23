# Third Party Library
from tortoise import fields

# First Library
import mixins
from common.models import BaseModel


class Contact(mixins.ContactMixin, BaseModel):
    """
    contact is a method of notification.

    like mobile, email, slack, etc.
    """

    name = fields.CharField(max_length=255)
    code = fields.CharField(max_length=255, unique=True)
    description = fields.TextField()
    definition = fields.JSONField(default=dict)

    class Meta:
        table = "contacts"

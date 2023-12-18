# Third Party Library
from tortoise import fields

# First Library
from common.models import BaseModel


class EndUser(BaseModel):
    external_id = fields.CharField(max_length=255, unique=True)
    endpoints = fields.ManyToManyField(
        "models.Contact",
        related_name="endpoints",
        through="models.Endpoint",
    )

    class Meta:
        table = "end_users"

# Third Party Library
from message import mixins
from message.common.models import BaseModel
from tortoise import fields
from tortoise.contrib.postgres.indexes import GinIndex


class ProviderTemplate(mixins.ProviderTemplateMixin, BaseModel):
    """
    Provider Template Model respresents a template for a kind of provider.

    provider template cannot be deleted
    """

    name = fields.CharField(max_length=255)
    code = fields.CharField(max_length=255)
    logo = fields.TextField(null=True)
    description = fields.TextField(null=True)
    connection_definition = fields.JSONField(default=dict)
    message_definition = fields.JSONField(default=dict)

    contacts = fields.ManyToManyField(
        "models.Contact",
        related_name="provider_templates",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "provider_templates"
        unique_together = ("code", "deleted_at")


class Provider(mixins.ProviderMixin, BaseModel):
    """
    Provider Model represents a provider instance.

    provider can be deleted
    """

    provider_template = fields.ForeignKeyField("models.ProviderTemplate")
    alias = fields.CharField(max_length=255)
    tags = fields.JSONField(default=list)
    connection_params = fields.JSONField(default=dict)

    class Meta:
        table = "providers"
        unique_together = ("provider_template", "alias", "deleted_at")
        indexes = (GinIndex(fields=["tags"]),)

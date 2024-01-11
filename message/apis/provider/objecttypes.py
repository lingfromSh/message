# Standard Library
import enum

# Third Party Library
import strawberry
from message import models
from message.common.graphql.relay import TortoiseORMNode


class ProviderTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Provider


ProviderCodeEnum = enum.Enum(
    "ProviderCodeEnum", {code: code for code in models.Provider.get_provider_codes()}
)

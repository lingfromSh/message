# Third Party Library
from message import models
from message.common.graphql.relay import TortoiseORMNode


class ProviderTemplateTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.ProviderTemplate


class ProviderTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Provider

# Third Party Library
from message import models
from message.common.graphql.relay import TortoiseORMNode


class ProviderTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Provider

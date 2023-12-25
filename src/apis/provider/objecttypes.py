# First Library
import models
from common.graphql.relay import TortoiseORMNode


class ProviderTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Provider

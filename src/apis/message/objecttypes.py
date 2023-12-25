# First Library
import models
from common.graphql.relay import TortoiseORMNode


class MessageTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Message

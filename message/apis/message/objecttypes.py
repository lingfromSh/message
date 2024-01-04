# Third Party Library
from message import models
from message.common.graphql.relay import TortoiseORMNode


class MessageTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Message

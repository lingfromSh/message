# Third Party Library
from message import models
from message.common.graphql.relay import TortoiseORMNode


class EndpointTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Endpoint

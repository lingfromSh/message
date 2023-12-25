# First Library
import models
from common.graphql.relay import TortoiseORMNode


class EndpointTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Endpoint

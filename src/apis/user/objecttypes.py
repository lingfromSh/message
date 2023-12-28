# Standard Library
import typing

# Third Party Library
import strawberry
from strawberry import relay

# First Library
import models
from common.graphql.relay import TortoiseORMNode
from common.graphql.scalar import ULID


class UserTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.User


@strawberry.input
class UserEndpointAddInput:
    contact: relay.GlobalID
    value: strawberry.scalars.JSON = None


@strawberry.input
class UserEndpointUpdateInput:
    id: typing.Optional[relay.GlobalID] = None
    contact: typing.Optional[relay.GlobalID] = None
    value: typing.Optional[strawberry.scalars.JSON] = None

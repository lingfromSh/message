# Standard Library
import typing

# Third Party Library
import strawberry
from message import models
from message.common.graphql.relay import TortoiseORMNode
from message.common.graphql.scalar import ULID
from strawberry import relay


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

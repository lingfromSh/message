from datetime import datetime
from typing import Generic
from typing import Optional

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID
from strawberry.relay import NodeType

from apps.message.common.constants import MessageProviderType
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.validators.provider import ProviderOutputModel
from infrastructures.graphql import ObjectID


@strawberry.type
class MessageNode(Node):
    ...


@strawberry.experimental.pydantic.type(
    model=ProviderOutputModel, use_pydantic_alias=False
)
class ProviderNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    code: strawberry.auto
    name: strawberry.auto
    type: strawberry.enum(MessageProviderType)

    config: Optional[strawberry.scalars.JSON]

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_pydantic(output: ProviderOutputModel, extra):
        return ProviderNode(global_id=output.oid, **output.model_dump())

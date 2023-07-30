from datetime import datetime
from typing import Generic
from typing import Iterable
from typing import Optional

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID
from strawberry.relay import NodeType
from strawberry.relay.utils import from_base64
from strawberry.types.info import Info  # noqa: TCH001
from umongo.fields import Reference

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.validators.message import MessageOutputModel
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

    @classmethod
    async def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ):
        nodes = []
        async for provider in Provider.find({"_id": {"$in": node_ids}}):
            node = cls.from_pydantic(ProviderOutputModel.model_validate(provider))
            nodes.append(node)

        return nodes


async def ref_provider(root: "MessageNode"):
    if isinstance(root.provider, Reference):
        provider = await root.provider.fetch()
        return ProviderOutputModel.model_validate(provider)


@strawberry.experimental.pydantic.type(
    model=MessageOutputModel, use_pydantic_alias=False
)
class MessageNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    provider: ProviderNode = strawberry.field(resolver=ref_provider)
    realm: strawberry.scalars.JSON
    status: strawberry.enum(MessageStatus)

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_pydantic(output: MessageOutputModel, extra):
        return MessageNode(global_id=output.id, **output.model_dump())

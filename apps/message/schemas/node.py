from datetime import datetime
from typing import Iterable
from typing import Optional

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID
from strawberry.types.info import Info  # noqa: TCH001
from umongo.fields import Reference
from typing import Annotated
from bson.objectid import ObjectId

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.models import Provider
from infrastructures.graphql import ObjectID
from infrastructures.graphql import document_to_node


@strawberry.type
class ProviderNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    code: str
    name: str
    type: strawberry.enum(MessageProviderType)

    config: Optional[strawberry.scalars.JSON]

    created_at: datetime
    updated_at: datetime

    @classmethod
    async def resolve_nodes(
        cls, *, info: Info, node_ids: Iterable[str], required: bool = False
    ):
        print(node_ids)
        ret = []
        async for provider in Provider.find({"_id": {"$in": node_ids}}):
            ret.append(document_to_node(provider))
        return ret


async def ref_provider(root: "MessageNode"):
    if isinstance(root.provider, Reference):
        provider = await root.provider.fetch()
    elif isinstance(root.provider, str):
        provider = await Provider.find_one({"_id": ObjectId(root.provider)})
    else:
        provider = await Provider.find_one({"_id": root.provider})
    data = provider.dump()
    data["global_id"] = data.pop("id")
    data["oid"] = data["global_id"]
    return ProviderNode(**data)


@strawberry.type
class MessageNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    provider: ProviderNode = strawberry.field(resolver=ref_provider)
    realm: strawberry.scalars.JSON
    status: strawberry.enum(MessageStatus)

    created_at: datetime
    updated_at: datetime

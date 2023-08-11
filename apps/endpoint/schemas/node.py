from typing import List
from typing import Optional

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID

from apps.endpoint.validators.endpoint import EndpointOutputModel
from infrastructures.graphql import ObjectID


@strawberry.experimental.pydantic.type(
    model=EndpointOutputModel, use_pydantic_alias=False
)
class EndpointNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    external_id: strawberry.auto
    tags: strawberry.auto

    websockets: strawberry.auto
    emails: Optional[List[str]]

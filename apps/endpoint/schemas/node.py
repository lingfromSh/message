from typing import List
from typing import Optional

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID

from infrastructures.graphql import ObjectID


@strawberry.type
class EndpointNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[str]]

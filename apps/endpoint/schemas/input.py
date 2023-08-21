from typing import List
from typing import Optional

import strawberry


@strawberry.input
class CreateEndpointInput:
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[str]]


@strawberry.input
class UpdateEndpointInput:
    external_id: str
    tags: Optional[List[str]] = None

    websockets: Optional[List[str]] = None
    emails: Optional[List[str]] = None


@strawberry.input
class DestroyEndpointInput:
    oids: Optional[List[str]] = None
    external_ids: Optional[List[str]] = None

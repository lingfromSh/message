import strawberry
import dataclasses
from typing import List, Optional
from apps.endpoint.validators.endpoint import (
    CreateEndpointInputModel,
    UpdateEndpointInputModel,
    DestroyEndpointInputModel,
)


@strawberry.input
class CreateEndpointInput:
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[str]]

    def to_pydantic(self) -> CreateEndpointInputModel:
        data = dataclasses.asdict(self)
        return CreateEndpointInputModel.model_validate(data)


@strawberry.input
class UpdateEndpointInput:
    external_id: str
    tags: Optional[List[str]] = None

    websockets: Optional[List[str]] = None
    emails: Optional[List[str]] = None

    def to_pydantic(self) -> UpdateEndpointInputModel:
        data = dataclasses.asdict(self)
        return UpdateEndpointInputModel.model_validate(data)


@strawberry.input
class DestroyEndpointInput:
    oids: Optional[List[str]] = None
    external_ids: Optional[List[str]] = None

    def to_pydantic(self) -> DestroyEndpointInputModel:
        data = dataclasses.asdict(self)
        return DestroyEndpointInputModel.model_validate(data)

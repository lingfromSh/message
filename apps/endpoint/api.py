import strawberry
from typing import Optional, List, AsyncIterable
from apps.endpoint.models import Endpoint
from apps.endpoint.schemas.node import EndpointNode
from apps.endpoint.schemas.input import (
    CreateEndpointInput,
    UpdateEndpointInput,
    DestroyEndpointInput,
)
from apps.endpoint.validators.endpoint import EndpointOutputModel
from infrastructures.graphql import connection
from infrastructures.graphql import MessageConnection


@strawberry.type
class Query:
    @connection(MessageConnection[EndpointNode])
    async def endpoints(
        self, external_ids: Optional[List[str]] = None, tags: Optional[List[str]] = None
    ) -> AsyncIterable[EndpointNode]:
        conditions = {}
        if external_ids is not None:
            conditions["external_id"] = {"$in": external_ids}
        if tags is not None:
            conditions["tags"] = {"$in": tags}
        return Endpoint.find(conditions)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_endpoint(self, input: CreateEndpointInput) -> EndpointNode:
        model = input.to_pydantic()
        endpoint = await model.save()
        return EndpointOutputModel.model_validate(endpoint)

    @strawberry.mutation
    async def update_endpoint(self, input: UpdateEndpointInput) -> EndpointNode:
        model = input.to_pydantic()
        endpoint = await model.save()
        return EndpointOutputModel.model_validate(endpoint)

    @strawberry.mutation
    async def destroy_endpoints(self, input: DestroyEndpointInput) -> int:
        model = input.to_pydantic()
        return await model.delete()

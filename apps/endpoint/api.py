import dataclasses
from typing import AsyncIterable
from typing import List
from typing import Optional

import strawberry
from strawberry.types import Info

from apps.endpoint.models import Endpoint
from apps.endpoint.schemas.input import CreateEndpointInput
from apps.endpoint.schemas.input import DestroyEndpointInput
from apps.endpoint.schemas.input import UpdateEndpointInput
from apps.endpoint.schemas.node import EndpointNode
from infrastructures.graphql import MessageConnection
from infrastructures.graphql import connection


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
        endpoint = Endpoint(**dataclasses.asdict(input))
        await endpoint.commit()
        return EndpointNode(
            global_id=endpoint.pk,
            oid=endpoint.pk,
            external_id=input.external_id,
            tags=input.tags,
            websockets=input.websockets,
            emails=input.emails,
        )

    @strawberry.mutation
    async def update_endpoint(
        self, info: Info, input: UpdateEndpointInput
    ) -> EndpointNode:
        request = info.context.get("request")
        app = request.app

        async def atomic_update(session):
            endpoint = await Endpoint.find_one({"external_id": input.external_id})
            if not endpoint:
                return None
            if input.tags:
                endpoint.tags = input.tags
            if input.websockets:
                endpoint.websockets = input.websockets
            if input.emails:
                endpoint.emails = input.emails

            if change := endpoint.to_mongo(update=True):
                await Endpoint.collection.update_one(
                    {"external_id": input.external_id},
                    change,
                    session=session,
                )
            return endpoint

        async with await app.ctx.db_client.start_session() as session:
            updated = await session.with_transaction(atomic_update)
            if updated:
                return EndpointNode(
                    global_id=updated.pk,
                    oid=updated.pk,
                    external_id=updated.external_id,
                    tags=updated.tags,
                    websockets=updated.websockets,
                    emails=updated.emails,
                )
            raise ValueError("endpoint not found")

    @strawberry.mutation
    async def destroy_endpoints(self, input: DestroyEndpointInput) -> int:
        conditions = []
        if input.oids:
            conditions.append({"_id": {"$in": input.oids}})
        if input.external_ids:
            conditions.append({"external_id": {"$in": input.external_ids}})
        if conditions:
            destoried = await Endpoint.collection.delete_many({"$or": conditions})
            return destoried.deleted_count
        return 0

# Standard Library
import typing

# Third Party Library
import strawberry
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from message.exceptions.endpoint import EndpointNotFoundError
from message.wiring import ApplicationContainer
from strawberry import relay

# Local Folder
from .objecttypes import EndpointTortoiseORMNode


@strawberry.type(description="Endpoint API")
class Query:
    @connection(TortoiseORMPaginationConnection[EndpointTortoiseORMNode])
    async def endpoints(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        user_ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        contact_ids: typing.Optional[typing.List[relay.GlobalID]] = None,
    ) -> typing.AsyncIterable[EndpointTortoiseORMNode]:
        application = ApplicationContainer.endpoint_application()
        conditions = {}
        if ids:
            conditions["id__in"] = [id.node_id for id in ids]
        if user_ids:
            conditions["user_id__in"] = [id.node_id for id in user_ids]
        if contact_ids:
            conditions["contact_id__in"] = [id.node_id for id in contact_ids]
        return await application.get_many(conditions)


@strawberry.type(description="Endpoint API")
class Mutation:
    @strawberry.mutation(description="Import endpoints", deprecation_reason="not ready")
    async def endpoint_import(self) -> str:
        return "not ready"

    @strawberry.mutation(description="Create endpoint")
    async def endpoint_create(
        self,
        user_id: relay.GlobalID,
        contact_id: relay.GlobalID,
        value: strawberry.scalars.JSON,
    ) -> EndpointTortoiseORMNode:
        application = ApplicationContainer.endpoint_application()
        endpoint = await application.create(
            user_id=user_id.node_id,
            contact_id=contact_id.node_id,
            value=value,
        )
        return await EndpointTortoiseORMNode.resolve_orm(endpoint)

    @strawberry.mutation(description="Update endpoint")
    async def endpoint_update(
        self, id: relay.GlobalID, value: strawberry.scalars.JSON
    ) -> EndpointTortoiseORMNode:
        application = ApplicationContainer.endpoint_application()
        endpoint = await application.get(id=id.node_id)
        if not endpoint:
            raise EndpointNotFoundError
        await application.update_endpoint(endpoint, value=value)
        return await EndpointTortoiseORMNode.resolve_orm(endpoint)

    @strawberry.mutation(description="Destory endpoints")
    async def endpoint_destroy(self, ids: typing.List[relay.GlobalID]) -> str:
        application = ApplicationContainer.endpoint_application()
        deleted = await application.delete_many(
            filters={"id__in": [int(id.node_id) for id in ids]}
        )
        return "ok" if deleted else "failed"

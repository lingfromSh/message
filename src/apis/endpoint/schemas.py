# Standard Library
import typing

# Third Party Library
import strawberry
from strawberry import relay

# First Library
import applications
from common.graphql.relay import TortoiseORMPaginationConnection
from common.graphql.relay import TortoiseORMPaginationConnectionExtension

# Local Folder
from .objecttypes import EndpointTortoiseORMNode


@strawberry.type(description="Endpoint API")
class Query:
    @relay.connection(
        TortoiseORMPaginationConnection[EndpointTortoiseORMNode],
        extensions=[TortoiseORMPaginationConnectionExtension()],
    )
    async def endpoints(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        user_ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        contact_ids: typing.Optional[typing.List[relay.GlobalID]] = None,
    ) -> typing.AsyncIterable[EndpointTortoiseORMNode]:
        application = applications.EndpointApplication()
        conditions = {}
        if ids:
            conditions["id__in"] = [id.node_id for id in ids]
        if user_ids:
            conditions["user_id__in"] = [id.node_id for id in user_ids]
        if contact_ids:
            conditions["contact_id__in"] = [id.node_id for id in contact_ids]
        return await application.get_endpoints(conditions)


@strawberry.type(description="Endpoint API")
class Mutation:
    @strawberry.mutation(description="Import endpoints", deprecation_reason="not ready")
    async def import_endpoints(self) -> str:
        return "not ready"

    @strawberry.mutation(description="Create endpoint")
    async def endpoint_create(
        self, user_id: relay.GlobalID, contact_id: relay.GlobalID
    ) -> EndpointTortoiseORMNode:
        application = applications.EndpointApplication()
        endpoint = application.create_endpoint(
            user_id=user_id.node_id,
            contact_id=contact_id.node_id,
        )
        return EndpointTortoiseORMNode.resolve_orm(endpoint)

    @strawberry.mutation(description="Update endpoint")
    async def endpoint_update(
        self, id: relay.GlobalID, value: strawberry.scalars.JSON
    ) -> EndpointTortoiseORMNode:
        application = applications.EndpointApplication()
        endpoint = await application.get_endpoint(id=id)
        await application.update_endpoint(endpoint, value=value)
        return EndpointTortoiseORMNode.resolve_orm(endpoint)

    @strawberry.mutation(description="Destory endpoints")
    async def endpoint_destroy(self, ids: typing.List[relay.GlobalID]) -> str:
        application = applications.EndpointApplication()
        await application.destory_endpoints(*ids)

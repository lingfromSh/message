# Standard Library
import typing

# Third Party Library
import strawberry
from strawberry import relay

# First Library
import applications
from common.graphql.relay import TortoiseORMPaginationConnection
from common.graphql.relay import connection

# Local Folder
from .objecttypes import ProviderTortoiseORMNode


@strawberry.type(description="Provider API")
class Query:
    @connection(TortoiseORMPaginationConnection[ProviderTortoiseORMNode])
    async def providers(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        name: typing.Optional[str] = None,
        code: typing.Optional[str] = None,
    ) -> typing.AsyncIterable[ProviderTortoiseORMNode]:
        application = applications.ProviderApplication()
        conditions = {}
        if ids is not None:
            conditions["id__in"] = [id.node_id for id in ids]
        if name is not None:
            conditions["name__icontains"] = name
        if code is not None:
            conditions["code__icontains"] = code
        return await application.get_providers(conditions)


@strawberry.type(description="Provider API")
class Mutation:
    @strawberry.mutation(description="Create provider")
    async def provider_create(
        self,
        code: str,
        name: str,
        description: typing.Optional[str] = None,
        params: typing.Optional[strawberry.scalars.JSON] = None,
    ) -> ProviderTortoiseORMNode:
        application = applications.ProviderApplication()
        provider = await application.create_provider(name, code, description, params)
        return await ProviderTortoiseORMNode.resolve_orm(provider)

    @strawberry.mutation(description="Destory providers")
    async def provider_destory(self, ids: typing.List[relay.GlobalID]) -> str:
        application = applications.ProviderApplication()
        return await application.destory_objs(*[id.node_id for id in ids])

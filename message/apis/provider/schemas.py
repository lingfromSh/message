# Standard Library
import typing

# Third Party Library
import strawberry
from message import applications
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from strawberry import relay

# Local Folder
from .objecttypes import ProviderCodeEnum
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
        code: strawberry.enum(ProviderCodeEnum),
        name: str,
        description: typing.Optional[str] = None,
        params: typing.Optional[strawberry.scalars.JSON] = None,
    ) -> ProviderTortoiseORMNode:
        application = applications.ProviderApplication()
        provider = await application.create_provider(
            name=name,
            code=code.value if code else None,
            description=description,
            params=params,
        )
        return await ProviderTortoiseORMNode.resolve_orm(provider)

    @strawberry.mutation(description="Update provider")
    async def provider_update(
        self,
        id: relay.GlobalID,
        code: typing.Optional[strawberry.enum(ProviderCodeEnum)] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        params: typing.Optional[strawberry.scalars.JSON] = None,
    ) -> ProviderTortoiseORMNode:
        application = applications.ProviderApplication()
        provider = await application.get_provider(id=id.node_id)
        await application.update_provider(
            provider,
            name=name,
            code=code.value if code else None,
            description=description,
            params=params,
        )
        return await ProviderTortoiseORMNode.resolve_orm(provider)

    @strawberry.mutation(description="Destory providers")
    async def provider_destory(self, ids: typing.List[relay.GlobalID]) -> str:
        application = applications.ProviderApplication()
        return await application.destory_objs(*[id.node_id for id in ids])

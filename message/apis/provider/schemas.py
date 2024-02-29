# Standard Library
import typing

# Third Party Library
import strawberry
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from message.wiring import ApplicationContainer
from strawberry import relay

# Local Folder
from .objecttypes import ProviderTemplateTortoiseORMNode
from .objecttypes import ProviderTortoiseORMNode


@strawberry.type(description="Provider Related API")
class Query:
    @connection(TortoiseORMPaginationConnection[ProviderTemplateTortoiseORMNode])
    async def provider_templates(
        self, code: typing.Optional[str] = None, name: typing.Optional[str] = None
    ) -> typing.AsyncIterator[ProviderTemplateTortoiseORMNode]:
        application = ApplicationContainer.provider_template_application()
        filters = {}
        if code is not None:
            filters["code"] = code
        if name is not None:
            filters["name"] = name
        return await application.get_many(filters=filters)

    @connection(TortoiseORMPaginationConnection[ProviderTortoiseORMNode])
    async def providers(
        self,
        template_id: typing.Optional[relay.GlobalID] = None,
        alias: typing.Optional[str] = None,
        tags: typing.Optional[typing.List[str]] = None,
    ) -> typing.AsyncIterator[ProviderTortoiseORMNode]:
        application = ApplicationContainer.provider_application()
        filters = {}
        if template_id is not None:
            filters["provider_template_id"] = int(template_id.node_id)
        if alias is not None:
            filters["alias"] = alias
        if tags is not None:
            filters["tags__overlap"] = tags
        return application.get_many(filters=filters)


@strawberry.type(description="Provider Template API")
class Mutation:
    @strawberry.mutation(description="Create a new provider")
    async def provider_create(
        self,
        template_id: relay.GlobalID,
        alias: str,
        connection_params: strawberry.scalars.JSON,
        tags: typing.Optional[typing.List[str]] = None,
    ) -> ProviderTortoiseORMNode:
        application = ApplicationContainer.provider_application()
        provider = await application.create(
            provider_template_id=int(template_id.node_id),
            alias=alias,
            connection_params=connection_params,
            tags=tags,
        )
        return await ProviderTortoiseORMNode.resolve_orm(provider)

    @strawberry.mutation(description="Update a provider")
    async def provider_update(
        self,
        template_id: relay.GlobalID,
        alias: str,
        connection_params: strawberry.scalars.JSON,
        tags: typing.Optional[typing.List[str]] = None,
    ) -> ProviderTortoiseORMNode:
        application = ApplicationContainer.product_application()
        provider_template_id = int(template_id.node_id)
        provider = await application.update(
            provider_template_id=provider_template_id,
            alias=alias,
            connection_params=connection_params,
            tags=tags,
        )
        return await ProviderTortoiseORMNode.resolve_orm(provider)

    @strawberry.mutation(description="Delete a provider")
    async def provider_destroy(self, ids: typing.List[relay.GlobalID]) -> bool:
        application = ApplicationContainer.provider_application()
        return await application.delete_many(
            filters={"id__in": [int(id.node_id) for id in ids]}
        )

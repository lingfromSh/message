# Standard Library
import typing

# Third Party Library
import strawberry
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from message.exceptions.user import UserNotFoundError
from message.wiring import ApplicationContainer
from strawberry import relay

# Local Folder
from .objecttypes import UserEndpointAddInput
from .objecttypes import UserEndpointUpdateInput
from .objecttypes import UserTortoiseORMNode


@strawberry.type(description="User API")
class Query:
    @strawberry.field
    async def user_get_by_external_id(self, external_id: str) -> UserTortoiseORMNode:
        application = ApplicationContainer.user_application()
        return await application.get_by_external_id(external_id)

    @connection(TortoiseORMPaginationConnection[UserTortoiseORMNode])
    async def users(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        external_ids: typing.Optional[typing.List[str]] = None,
        is_active: typing.Optional[bool] = None,
    ) -> typing.AsyncIterable[UserTortoiseORMNode]:
        application = ApplicationContainer.user_application()
        filters = {}
        if ids is not None:
            filters["id__in"] = [id.node_id for id in ids]
        if external_ids is not None:
            filters["external_id__in"] = external_ids
        if is_active is not None:
            filters["is_active"] = is_active
        return await application.get_many(filters=filters)


@strawberry.type(description="User API")
class Mutation:
    @strawberry.mutation(description="Register a new user")
    async def user_register(
        self,
        external_id: str,
        metadata: typing.Optional[strawberry.scalars.JSON] = None,
        endpoints: typing.Optional[typing.List[UserEndpointAddInput]] = None,
    ) -> UserTortoiseORMNode:
        application = ApplicationContainer.user_application()
        if metadata is None:
            metadata = {}
        if endpoints is None:
            endpoints = []

        # TODO: implement application create method
        created = await application.create(
            external_id=external_id,
            metadata=metadata,
            endpoints=[
                {"contact_id": int(endpoint.contact.node_id), "value": endpoint.value}
                for endpoint in endpoints
            ],
        )
        return await UserTortoiseORMNode.resolve_orm(created)

    @strawberry.mutation(description="Update user")
    async def user_update(
        self,
        id: relay.GlobalID,
        external_id: typing.Optional[str] = None,
        metadata: typing.Optional[strawberry.scalars.JSON] = None,
        is_active: typing.Optional[bool] = None,
        endpoints: typing.Optional[typing.List[UserEndpointUpdateInput]] = None,
    ) -> UserTortoiseORMNode:
        application = ApplicationContainer.user_application()
        user = await application.get(id=int(id.node_id))
        if not user:
            raise UserNotFoundError

        if endpoints:
            endpoints = [
                {
                    "id": int(endpoint.id.node_id) if endpoint.id else None,
                    "contact_id": (
                        int(endpoint.contact.node_id) if endpoint.contact else None
                    ),
                    "value": endpoint.value if endpoint.value else None,
                }
                for endpoint in endpoints
            ]

        await application.update(
            user,
            external_id=external_id,
            metadata=metadata,
            is_active=is_active,
            endpoints=endpoints,
        )
        return await UserTortoiseORMNode.resolve_orm(user)

    @strawberry.mutation(description="Delete users")
    async def user_destory(self, ids: typing.List[relay.GlobalID]) -> bool:
        application = ApplicationContainer.user_application()
        return await application.delete_many(
            filters={"id__in": [id.node_id for id in ids]}
        )

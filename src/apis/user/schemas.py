# Standard Library
import typing
from datetime import datetime

# Third Party Library
import strawberry
from strawberry import relay

# First Library
import applications
from common.graphql.relay import TortoiseORMPaginationConnection

# Local Folder
from .obecttypes import UserTortoiseORMNode


@strawberry.type(description="User API")
class Query:
    @strawberry.field
    async def user_get_by_external_id(self, external_id: str) -> UserTortoiseORMNode:
        application = applications.UserApplication()
        return await application.get_user_by_external_id(external_id)

    @relay.connection(TortoiseORMPaginationConnection[UserTortoiseORMNode])
    async def users(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        external_ids: typing.Optional[typing.List[str]] = None,
        created_at_before: typing.Optional[datetime] = None,
        created_at_after: typing.Optional[datetime] = None,
        updated_at_before: typing.Optional[datetime] = None,
        updated_at_after: typing.Optional[datetime] = None,
        is_active: typing.Optional[bool] = None,
    ) -> typing.AsyncIterable[UserTortoiseORMNode]:
        application = applications.UserApplication()
        conditions = {}
        if ids is not None:
            conditions["id__in"] = [id.node_id for id in ids]
        if external_ids is not None:
            conditions["external_id__in"] = external_ids
        if created_at_before is not None:
            conditions["created_at__lt"] = created_at_before
        if created_at_after is not None:
            conditions["created_at__gt"] = created_at_after
        if updated_at_before is not None:
            conditions["updated_at__lt"] = updated_at_before
        if updated_at_after is not None:
            conditions["updated_at__gt"] = updated_at_after
        if is_active is not None:
            conditions["is_active"] = is_active

        return application.get_users(conditions=conditions)


@strawberry.type(description="User API")
class Mutation:
    @strawberry.mutation(description="Register a new user")
    async def user_register(
        self,
        external_id: str,
        metadata: typing.Optional[strawberry.scalars.JSON] = None,
        endpoints: typing.Optional[typing.List[strawberry.scalars.JSON]] = None,
    ) -> UserTortoiseORMNode:
        application = applications.UserApplication()
        return await application.create_user(external_id=external_id, metadata=metadata)

    @strawberry.mutation(description="Update user")
    async def user_update(
        self,
        id: relay.GlobalID,
        external_id: typing.Optional[str] = None,
        metadata: typing.Optional[strawberry.scalars.JSON] = None,
        is_active: typing.Optional[bool] = None,
        endpoints: typing.Optional[typing.List[strawberry.scalars.JSON]] = None,
    ) -> UserTortoiseORMNode:
        application = applications.UserApplication()
        user = await application.get_user(id.node_id)
        await application.update_user(
            user,
            external_id=external_id,
            metadata=metadata,
            is_active=is_active,
            endpoints=endpoints,
        )
        # TODO: implement auto return type convertion
        return UserTortoiseORMNode.resolve_orm(user)

    @strawberry.mutation(description="Delete users")
    async def user_destory(
        self, ids: typing.Optional[typing.List[relay.GlobalID]]
    ) -> str:
        application = applications.UserApplication()
        return await application.destroy_users(*(id.node_id for id in ids))

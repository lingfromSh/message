# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from message import models
from message.helpers.decorators import ensure_infra
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from ulid import ULID

# Local Folder
from .base import ApplicationBase


class UserApplication(ApplicationBase[models.User]):
    def __init__(self, repository: typing.Type[models.User] = models.User):
        self.repository: typing.Type[models.User] = repository

    @ensure_infra("persistence")
    async def get_users(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> typing.AsyncIterable[models.User]:
        return await self.get_objs(
            conditions=conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    async def get_user(self, id: ULID) -> typing.Optional[models.User]:
        return await self.get_obj(id=id)

    async def get_user_by_external_id(
        self, external_id: str
    ) -> typing.Optional[models.User]:
        return await self.repository.from_external_id(external_id=external_id)

    @ensure_infra("persistence")
    async def create_user(
        self,
        external_id: str,
        metadata: typing.Optional[typing.Dict] = None,
        is_active: typing.Optional[bool] = None,
        endpoints: typing.Optional[typing.List[typing.Dict]] = None,
    ) -> models.User:
        async with in_transaction("default"):
            params = {}
            await self.repository.validate_external_id(external_id)
            if metadata is not None:
                params["metadata"] = metadata
            if is_active is not None:
                params["is_active"] = is_active

            domain = await self.repository.create(external_id=external_id, **params)
            if endpoints is not None:
                await domain.add_endpoints(*endpoints)

            return domain

    @ensure_infra("persistence")
    async def update_user(
        self,
        user: models.User,
        external_id: typing.Optional[str] = None,
        metadata: typing.Optional[typing.Dict] = None,
        is_active: typing.Optional[bool] = None,
        endpoints: typing.Optional[typing.List[typing.Dict]] = None,
    ) -> models.User:
        async with in_transaction():
            if external_id is not None:
                await user.set_external_id(external_id, save=False)
            if metadata is not None:
                await user.set_metadata(metadata, save=False)
            if is_active is not None and is_active:
                await user.activate(is_active, save=False)
            elif is_active is not None and is_active is False:
                await user.deactivate(is_active, save=False)
            if endpoints:
                await user.set_endpoints(*endpoints)
            await user.save(
                update_fields=[
                    "external_id",
                    "metadata",
                    "is_active",
                    "updated_at",
                ]
            )
            return user

    @ensure_infra("persistence")
    async def destroy_users(
        self, *ids: typing.List[ULID]
    ) -> typing.Literal["ok", "error"]:
        with suppress(Exception):
            async with in_transaction("default"):
                await self.repository.active_objects.select_for_update().filter(
                    id__in=ids
                ).update(is_deleted=True, deleted_at=now())
                return "ok"
        return "error"

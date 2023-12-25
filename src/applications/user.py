# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from ulid import ULID

# First Library
import exceptions
import models

# Local Folder
from .base import ApplicationBase


class UserApplication(ApplicationBase[models.User]):
    def __init__(self, repository: typing.Type[models.User] = models.User):
        self.repository: typing.Type[models.User] = repository

    async def get_users(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> typing.AsyncIterable[models.User]:
        qs = self.repository.active_objects.filter(**conditions)
        if offset is not None:
            qs = qs.offset(offset)
        if limit is not None:
            qs = qs.limit(limit)
        if order_by is not None:
            qs = qs.order_by(*order_by)
        if for_update:
            qs = qs.select_for_update()
        return qs

    async def get_user(self, id: ULID) -> typing.Optional[models.User]:
        return await self.repository.from_id(id=id)

    async def get_user_by_external_id(
        self, external_id: str
    ) -> typing.Optional[models.User]:
        return await self.repository.from_external_id(external_id=external_id)

    async def create_user(
        self,
        external_id: str,
        metadata: typing.Optional[typing.Dict] = None,
        is_active: typing.Optional[bool] = None,
        endpoints: typing.Optional[typing.List[typing.Dict]] = None,
    ) -> models.User:
        async with in_transaction():
            params = {}
            if await self.repository.active_objects.filter(
                external_id=external_id
            ).exists():
                raise exceptions.UserDuplicatedExternalIDError
            if metadata is not None:
                params["metadata"] = metadata
            if is_active is not None:
                params["is_active"] = is_active
            # TODO: handle endpoints
            return await self.repository.create(external_id=external_id, **params)

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
            if is_active is not None:
                await user.set_is_active(is_active, save=False)
            await user.save(update_fields=["external_id", "metadata", "is_active"])
            return user

    async def destroy_users(
        self, *ids: typing.List[ULID]
    ) -> typing.Literal["ok", "error"]:
        with suppress(Exception):
            async with in_transaction():
                await self.repository.active_objects.select_for_update().filter(
                    id__in=ids
                ).update(is_deleted=True, deleted_at=now())
                return "ok"
        return "error"

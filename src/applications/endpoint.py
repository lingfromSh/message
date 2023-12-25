# Standard Library
import typing

# Third Party Library
from tortoise.queryset import QuerySet
from ulid import ULID

# First Library
import models

# Local Folder
from .base import ApplicationBase


class EndpointApplication(ApplicationBase[models.Endpoint]):
    def get_endpoints(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[models.Endpoint]:
        return self.get_objs(
            conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    async def get_endpoint(self, id: ULID) -> models.Endpoint:
        return await self.get_obj(id)

    async def create_endpoint(
        self, user_id: ULID, contact_id: ULID, contact: typing.Any
    ) -> models.Endpoint:
        domain = await self.repository.create(
            user_id=user_id,
            contact_id=contact_id,
            value=contact,
        )
        return domain

    async def update_endpoint(
        self,
        endpoint: models.Endpoint,
        value: typing.Optional[typing.Any] = None,
    ) -> models.Endpoint:
        if value is not None:
            await endpoint.set_value(value=value)
        return endpoint

    async def destory_endpoints(
        self, *ids: typing.List[ULID]
    ) -> typing.Literal["ok", "error"]:
        return await self.destory_objs(*ids)

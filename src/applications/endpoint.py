# Standard Library
import typing

# Third Party Library
from tortoise.queryset import QuerySet
from ulid import ULID

# First Library
import exceptions
import models
from helpers.decorators import ensure_infra

# Local Folder
from .base import ApplicationBase


class EndpointApplication(ApplicationBase[models.Endpoint]):
    def __init__(self, repository: models.Endpoint = models.Endpoint):
        super().__init__(repository)

    @ensure_infra("persistence")
    async def get_endpoints(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[models.Endpoint]:
        return await self.get_objs(
            conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    @ensure_infra("persistence")
    async def get_endpoints_by_user_id(
        self, user_id: ULID
    ) -> QuerySet[models.Endpoint]:
        return await self.get_objs(
            conditions={"user_id": user_id},
        )

    @ensure_infra("persistence")
    async def get_endpoints_by_contact_id(
        self, contact_id: ULID
    ) -> QuerySet[models.Endpoint]:
        return await self.get_objs(
            conditions={"contact_id": contact_id},
        )

    @ensure_infra("persistence")
    async def get_endpoint(self, id: ULID) -> models.Endpoint:
        return await self.get_obj(id)

    @ensure_infra("persistence")
    async def create_endpoint(
        self, user_id: ULID, contact_id: ULID, value: typing.Any
    ) -> models.Endpoint:
        user_application = self.other(name="user")
        user_domain = await user_application.get_obj(id=user_id)
        contact_application = self.other(name="contact")
        contact_domain = await contact_application.get_obj(id=contact_id)
        validated_result = await contact_domain.validate_contact(value)
        if not validated_result.valid:
            raise exceptions.EndpointContactIsNotValidError
        domain = await self.repository.create(
            user=user_domain,
            contact=contact_domain,
            value=value,
        )
        return domain

    @ensure_infra("persistence")
    async def update_endpoint(
        self,
        endpoint: models.Endpoint,
        value: typing.Optional[typing.Any] = None,
    ) -> models.Endpoint:
        if value is not None:
            await endpoint.set_value(value=value)
        return endpoint

    @ensure_infra("persistence")
    async def destory_endpoints(
        self, *endpoints: typing.List[models.Endpoint]
    ) -> typing.Literal["ok", "error"]:
        return await self.destory_objs(*(endpoint.id for endpoint in endpoints))

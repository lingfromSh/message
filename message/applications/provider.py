# Standard Library
import typing

# Third Party Library
import backoff
from message import models
from message.helpers.decorators import ensure_infra
from tortoise.queryset import QuerySet
from tortoise.transactions import atomic
from ulid import ULID

# Local Folder
from .base import Application


class ProviderApplication(Application[models.Provider]):
    def __init__(self, repository: models.Provider = models.Provider):
        super().__init__(repository)

    @ensure_infra("persistence")
    async def get_providers(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[models.Provider]:
        return await self.get_objs(
            conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    @ensure_infra("persistence")
    async def get_provider(self, id: ULID) -> models.Provider:
        return await super().get_domain(id=id)

    @ensure_infra("persistence")
    @atomic("default")
    async def create_provider(
        self,
        *,
        name: str,
        code: str,
        description: typing.Optional[str] = None,
        params: typing.Optional[typing.Any] = None,
    ) -> models.Provider:
        return await self.repository.create_from_template(
            code,
            name=name,
            description=description,
            params=params,
        )

    @ensure_infra("persistence")
    @atomic("default")
    async def update_provider(
        self,
        provider: models.Provider,
        *,
        name: typing.Optional[str] = None,
        code: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        params: typing.Optional[typing.Any] = None,
    ):
        if name is not None:
            await provider.set_name(name, save=False)
        if code is not None:
            await provider.set_code(code, save=False)
        if description is not None:
            await provider.set_description(description, save=False)
        if params is not None:
            await provider.set_params(params, save=False)
        await provider.save(
            update_fields=[
                "name",
                "code",
                "description",
                "params",
                "updated_at",
            ]
        )
        return provider

    @backoff.on_exception(backoff.expo, Exception, max_tries=5)
    @ensure_infra("queue")
    @ensure_infra("persistence")
    async def send_message(
        self,
        provider: models.Provider,
        *,
        message,
        users=None,
        endpoints=None,
        contacts=None,
    ) -> ULID:
        """
        send message to users, endpoints or contacts
        """
        return await provider.send_message(
            message=message,
            users=users,
            endpoints=endpoints,
            contacts=contacts,
        )

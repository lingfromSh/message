# Standard Library
import typing

# Third Party Library
from blinker import signal
from message import models
from message.common.constants import SIGNALS
from message.helpers.decorators import ensure_infra
from tortoise.queryset import QuerySet
from tortoise.transactions import atomic
from ulid import ULID

# Local Folder
from .base import ApplicationBase


class MessageApplication(ApplicationBase[models.Message]):
    def __init__(self, repository: models.Message = models.Message):
        super().__init__(repository)

    def generate_message_id(self) -> str:
        return str(ULID())

    async def get_messages(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[models.Message]:
        return self.get_objs(
            conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    @ensure_infra("persistence")
    async def get_message(self, id: ULID) -> models.Message:
        return await super().get_obj(id=id)

    async def send_message(
        self,
        *,
        provider,
        content,
        users=None,
        endpoints=None,
        contacts=None,
    ) -> ULID:
        # TODO: send task with const name to avoid circular improt error
        # Third Party Library

        message_id = self.generate_message_id()
        await signal(SIGNALS.MESSAGE_CREATE).send_async(
            self,
            message_id=message_id,
            provider_id=provider,
            content=content,
            users=users,
            endpoints=endpoints,
            contacts=contacts,
        )
        return message_id

    @ensure_infra("persistence")
    async def create_message(
        self,
        id,
        provider,
        content,
        users=None,
        endpoints=None,
        contacts=None,
    ) -> models.Message:
        message = await self.repository.create(
            id=id,
            provider=provider,
            content=content,
            contacts=contacts,
        )
        if users is not None:
            await message.add_users(*users)
        if endpoints is not None:
            await message.add_endpoints(*endpoints)
        await message.mark_as_pending()
        return message

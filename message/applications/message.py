# Standard Library
import typing

# Third Party Library
from blinker import signal
from message import exceptions
from message import models
from message.common.constants import SIGNALS
from message.helpers.decorators import ensure_infra
from tortoise.queryset import QuerySet
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
        provider_id,
        content,
        users=None,
        endpoints=None,
        contacts=None,
    ) -> ULID:
        message_id = self.generate_message_id()
        # TODO: check with cache first, db operation is too slow
        # precheck params
        provider_application = self.other("provider")
        provider_domain = await provider_application.get_provider(id=provider_id)
        provider_domain.provider.validate_message(content)

        if users:
            user_application = self.other("user")
            no_users = not await (
                await user_application.get_users(conditions={"id__in": users})
            ).exists()
        else:
            no_users = True

        if endpoints:
            endpoint_application = self.other("endpoint")
            no_endpoints = not await (
                await endpoint_application.get_endpoints(
                    conditions={"id__in": endpoints}
                )
            ).exists()
        else:
            no_endpoints = True

        if contacts:
            no_contacts = not provider_domain.provider.validate_contacts(contacts)
        else:
            no_contacts = True

        if all([no_users, no_endpoints, no_contacts]):
            raise exceptions.MessageSendRequiredReceiversError

        await signal(SIGNALS.MESSAGE_CREATE).send_async(
            self,
            message_id=message_id,
            provider_id=provider_id,
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
        if contacts is None:
            contacts = []

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

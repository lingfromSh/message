# Standard Library
import asyncio

# Third Party Library
from message import exceptions
from message.common.constants import MessageStatusEnum
from tortoise.timezone import now
from ulid import ULID


class MessageMixin:
    @classmethod
    async def from_id(cls, id: ULID):
        domain = await cls.get_or_none(id=id).prefetch_related("provider")
        if domain is None:
            raise exceptions.MessageNotFoundError
        return domain

    @property
    def repository(self):
        return self.__class__

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    @classmethod
    async def acreate(
        cls,
        id,
        provider,
        content,
        users=None,
        endpoints=None,
        contacts=None,
    ):
        if contacts is None:
            contacts = []
        domain = cls(
            id=id,
            provider=provider,
            content=content,
            contacts=contacts,
        )
        await domain.mark_as_pending(save=False)
        await domain.save()
        if users is not None:
            await domain.add_users(*users)
        if endpoints is not None:
            await domain.add_endpoints(*endpoints)
        await domain.created.send_async(domain)
        return domain

    async def mark_as_pending(self, save: bool = True):
        await self.set_status(MessageStatusEnum.PENDING, save=save)

    async def mark_as_scheduled(self, save: bool = True):
        await self.set_status(MessageStatusEnum.SCHEDULED, save=save)

    async def mark_as_sending(self, save: bool = True):
        await self.set_status(MessageStatusEnum.SENDING, save=save)

    async def mark_as_succeeded(self, save: bool = True):
        await self.set_status(MessageStatusEnum.SUCCEEDED, save=save)

    async def mark_as_failed(self, save: bool = True):
        await self.set_status(MessageStatusEnum.FAILED, save=save)

    async def add_users(self, *users):
        await self.end_users.add(*users)

    async def add_endpoints(self, *endpoints):
        await self.endpoints.add(*endpoints)

    async def set_status(self, status: MessageStatusEnum, save: bool = True):
        status_history = self.status_history if self.status_history else []
        status_history.append({"status": status.value, "at": now()})

        if save:
            await self.db.update(
                status=status,
                status_history=status_history,
            )
        else:
            self.status = status
            self.status_history = status_history

# Third Party Library
from tortoise.timezone import now
from ulid import ULID

# First Library
import exceptions
from common.constants import MessageStatusEnum


class MessageMixin:
    @classmethod
    async def from_id(cls, id: ULID):
        domain = await cls.get_or_none(id=id)
        if domain is None:
            raise exceptions.MessageNotFoundError
        return domain

    @property
    def repository(self):
        return self.__class__

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    async def mark_as_pending(self):
        await self.set_status(MessageStatusEnum.PENDING)

    async def mark_as_scheduled(self):
        await self.set_status(MessageStatusEnum.SCHEDULED)

    async def mark_as_sending(self):
        await self.set_status(MessageStatusEnum.SENDING)

    async def mark_as_succeeded(self):
        await self.set_status(MessageStatusEnum.SUCCEEDED)

    async def mark_as_failed(self):
        await self.set_status(MessageStatusEnum.FAILED)

    async def add_users(self, *users):
        await self.end_users.add(*users)

    async def add_endpoints(self, *endpoints):
        await self.endpoints.add(*endpoints)

    async def set_status(self, status: MessageStatusEnum, save: bool = True):
        status_history = self.status_history
        status_history.append({"status": status.value, "at": now()})

        if save:
            await self.db.update(
                status=status,
                status_history=status_history,
            )
        else:
            self.status = status
            self.status_history = status_history

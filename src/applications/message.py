# Standard Library
import typing

# Third Party Library
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction
from ulid import ULID

# First Library
import models

# Local Folder
from .base import ApplicationBase


class MessageApplication(ApplicationBase[models.Message]):
    def __init__(self, repository: models.Message = models.Message):
        super().__init__(repository)

    def get_messages(
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

    async def get_message(self, id: ULID) -> models.Message:
        return await super().get_obj(id=id)

    async def generate_message_id(self) -> ULID:
        return ULID()

    async def create_message(
        self,
        provider,
        *,
        message,
        users=None,
        endpoints=None,
        contacts=None,
        background: bool = True,
    ) -> typing.Union[ULID, models.Message]:
        """
        if background is True, return message id only and return message id only.
        """

        async def wrapped_create_message(
            message_id,
            *,
            provider,
            content,
            users,
            endpoints,
            contacts,
            background_scheduler,
        ):
            message = None
            async with in_transaction("default"):
                message = await self.repository.create(
                    id=message_id,
                    provider=provider,
                    content=content,
                    contacts=contacts,
                )
                await message.mark_as_pending()
                if users:
                    await message.add_users(*users)
                if endpoints:
                    await message.add_endpoints(*endpoints)

            if message:
                background_scheduler.run_task_in_async_executor(
                    message.created.send_async,
                    args=(message,),
                )
            return message

        if background:
            message_id = await self.generate_message_id()
            background_scheduler = await self.infra.background_scheduler()
            background_scheduler.run_task_in_process_executor(
                wrapped_create_message,
                args=(message_id,),
                kwargs={
                    "provider": provider,
                    "content": message,
                    "contacts": contacts,
                    "users": users,
                    "endpoints": endpoints,
                    "background_scheduler": background_scheduler,
                },
            )
            return message_id
        else:
            return wrapped_create_message(
                message_id,
                provider,
                message,
                users,
                endpoints,
                background_scheduler,
            )

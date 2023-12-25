# Standard Library
import typing

# Third Party Library
from tortoise.queryset import QuerySet
from ulid import ULID

# First Library
import models

# Local Folder
from .base import ApplicationBase


class MessageApplication(ApplicationBase[models.Message]):
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
        return await self.repository.from_id(id=id)

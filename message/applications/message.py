# Standard Library
import typing

# Third Party Library
from message import exceptions
from message import models
from message.common.constants import SIGNALS
from message.helpers.decorators import ensure_infra
from tortoise.queryset import QuerySet
from ulid import ULID

# Local Folder
from .base import Application


class MessageApplication(Application[models.Message], repository=models.Message):
    def get_messages(
        self,
        conditions: typing.Dict = None,
        *,
        offset: int = None,
        limit: int = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[models.Message]:
        return super().get_domains(
            conditions=conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    @ensure_infra("persistence")
    async def get_message(self, id: ULID) -> models.Message:
        if domain := await super().get_domain(id=id):
            return domain
        raise exceptions.MessageNotFoundError

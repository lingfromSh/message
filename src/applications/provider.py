# Standard Library
import typing
from typing import List

# Third Party Library
from tortoise.queryset import QuerySet
from ulid import ULID

# First Library
import models

# Local Folder
from .base import ApplicationBase


class ProviderApplication(ApplicationBase[models.Provider]):
    def __init__(self, repository: models.Provider = models.Provider):
        super().__init__(repository)

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

    async def get_provider(self, id: ULID) -> models.Provider:
        return await self.repository.from_id(id=id)

    async def create_provider(
        self,
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

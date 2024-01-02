# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from tortoise import Model
from tortoise.queryset import QuerySet
from tortoise.timezone import now
from ulid import ULID

# First Library
from infra import get_infra

T = typing.TypeVar("T", bound=Model)


class ApplicationBase(typing.Generic[T]):
    __registry__ = {}

    def __init__(self, repository: T = T):
        self.repository: T = repository
        self.infra = get_infra()

    def __init_subclass__(cls) -> None:
        clsname = cls.__name__.replace("Application", "").lower()
        ApplicationBase.__registry__[clsname] = cls
        return cls

    def other(
        self, name: typing.Literal["contact", "endpoint", "user", "provider"]
    ) -> "ApplicationBase":
        return ApplicationBase.__registry__[name]()

    async def get_objs(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[T]:
        qs = self.repository.active_objects.filter(**conditions)
        if offset is not None:
            qs = qs.offset(offset)
        if limit is not None:
            qs = qs.limit(limit)
        if order_by is not None:
            qs = qs.order_by(*order_by)
        if for_update:
            qs = qs.select_for_update()
        return qs

    async def get_obj(self, id: ULID) -> typing.Optional[T]:
        return await self.repository.from_id(id=id)

    async def destory_objs(
        self,
        *ids: typing.List[ULID],
        real: bool = False,
    ) -> typing.Literal["ok", "error"]:
        with suppress(Exception):
            qs = self.repository.active_objects.select_for_update().filter(id__in=ids)
            if real:
                await qs.delete()
            else:
                await qs.update(is_deleted=True, deleted_at=now())
            return "ok"
        return "error"

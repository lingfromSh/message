# Future Library
from __future__ import annotations

# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from tortoise import Model
from ulid import ULID

Model = typing.TypeVar("Model", bound=Model)


class NotAssigned:
    ...


class Domain(metaclass=ABCMeta):
    def __init__(self, id: ULID = None):
        self.id = id or ULID()

    async def model_dump(self) -> Model:
        raise NotImplementedError


class Repository(typing.Generic[Model], metaclass=ABCMeta):
    model_class: Model = NotAssigned

    def __new__(cls, *args, **kwargs):
        assert (
            "model_class" in kwargs and kwargs["model_class"] != NotAssigned
        ), "model_class must be assigned"
        assert isinstance(
            kwargs["model_class"], Model
        ), "model_class must be a type of Model"
        return super().__new__(cls, *args, **kwargs)

    async def get(self, id: ULID) -> typing.Optional[Domain]:
        return await self.model_class.get_or_none(id=id)

    async def save(self, domain: Domain):
        instance = await domain.model_dump()
        await instance.save()

    async def delete(self, *ids: typing.List[ULID]) -> bool:
        row_affected = await self.model_class.filter(id__in=ids).delete()
        return row_affected == len(ids)


class Application(metaclass=ABCMeta):
    repository: Repository = NotAssigned

    async def get(self, id: ULID) -> typing.Optional[Domain]:
        return await self.repository.get(id)

    async def save(self, domain: Domain):
        await self.repository.save(domain)

    async def delete(self, *ids: typing.List[ULID]) -> bool:
        return await self.repository.delete(*ids)

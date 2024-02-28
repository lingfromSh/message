# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from message.common.models import BaseModel
from message.helpers.decorators import ensure_infra
from message.helpers.metaclasses import Singleton
from tortoise.queryset import QuerySet
from tortoise.timezone import now
from ulid import ULID

T = typing.TypeVar("T", bound=BaseModel)


class Application(typing.Generic[T], metaclass=Singleton):
    """
    Base class of Application

    Application provides methods for controling domain models.
    """

    def __init_subclass__(cls) -> None:
        """
        Require subclass to set `model_class` attribute.
        """
        assert hasattr(
            cls, "model_class"
        ), "subclass of Application must set `model_class` attribute"
        assert issubclass(
            cls.model_class, BaseModel
        ), "model_class attribute must be a subclass of BaseModel"
        cls.__annotations__["model_class"] = cls.model_class

    @ensure_infra("persistence")
    async def get(self, id: ULID) -> T | None:
        """
        Get a domain model by id.
        """
        return await self.model_class.active_objects.get_or_none(id=id)

    @ensure_infra("persistence")
    async def get_queryset(
        self,
        filters: dict,
        limit: int = None,
        offset: int = None,
        order_by: tuple[str] = None,
        for_update: bool = False,
        use_index: tuple[str] = None,
        use_db: str = None,
    ) -> QuerySet[T]:
        """
        Get domain queryset by filters.

        Args:
            filters (dict): Filters to apply to the query.
            for_update (bool): Whether to lock the rows for update.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.
            order_by (tuple[str]): Fields to order the results by.
            use_index (tuple[str]): Index to use for the query.
            use_db (str): Database to use for the query.

        Returns:
            QuerySet: A QuerySet object representing the domain models.
        """
        qs = self.model_class.active_objects.filter(**filters)
        if limit is not None and isinstance(limit, int) and limit >= 0:
            qs = qs.limit(limit)
        if offset is not None and isinstance(offset, int) and offset >= 0:
            qs = qs.offset(offset)
        if for_update:
            qs = qs.select_for_update()
        if (
            order_by is not None
            and isinstance(order_by, tuple)
            and all(isinstance(o, str) for o in order_by)
        ):
            qs = qs.order_by(*order_by)
        if (
            use_index is not None
            and isinstance(use_index, tuple)
            and all(isinstance(i, str) for i in use_index)
        ):
            qs = qs.using_index(*use_index)
        if use_db is not None and isinstance(use_db, str):
            qs = qs.using_db(use_db)
        return qs

    @ensure_infra("persistence")
    async def get_many(
        self,
        filters: dict,
        limit: int = None,
        offset: int = None,
        order_by: tuple[str] = None,
        for_update: bool = False,
        use_index: tuple[str] = None,
        use_db: str = None,
    ) -> typing.AsyncIterator[T]:
        """
        Get domain models by filters.
        """
        qs = await self.get_queryset(
            filters, limit, offset, order_by, for_update, use_index, use_db
        )
        return qs

    @ensure_infra("persistence")
    async def create(self, **kwargs) -> T:
        """
        Create a new domain model.
        """
        domain = self.model_class(**kwargs)
        await domain.validate(raise_exception=True)
        assert False
        await domain.save()
        return domain

    @ensure_infra("persistence")
    async def update(self, domain, **kwargs) -> T:
        """
        Update domain model
        """
        domain.update_from_dict(kwargs)
        await domain.validate()
        await domain.save()
        return domain

    @ensure_infra("persistence")
    async def delete(self, id: ULID) -> bool:
        """
        Delete domain models by id.
        """
        with suppress(Exception):
            await self.model_class.active_objects.filter(id__in=id).update(
                is_deleted=True, deleted_at=now()
            )
            return True
        return False

    @ensure_infra("persistence")
    async def delete_many(self, filters: dict) -> bool:
        """
        Delete domain models by filters.
        """
        with suppress(Exception):
            await self.model_class.active_objects.filter(**filters).update(
                is_deleted=True, deleted_at=now()
            )
            return True
        return False

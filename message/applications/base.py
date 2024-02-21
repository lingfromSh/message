# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from message.helpers.decorators import ensure_infra
from message.helpers.metaclasses import Singleton
from tortoise import Model
from tortoise.queryset import QuerySet
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from ulid import ULID

if typing.TYPE_CHECKING:
    # Third Party Library
    from infra import InfrastructureContainer

Repository = typing.TypeVar("Repository", bound=Model)


class Application(metaclass=Singleton):
    """
    Base class of Application

    Application provides methods for controling domain models.
    """

    _registry_ = {}
    REPOSITORY: typing.Type[Repository] = NotImplemented
    DOMAIN: Repository = NotImplemented

    def __init__(self, infra):
        self.infra = infra

    def __init_subclass__(cls) -> None:
        assert cls.REPOSITORY is not NotImplemented, "repository must be set"

    @property
    def transaction(self):
        return in_transaction(self.REPOSITORY._meta.default_connection)

    def get_domains(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> QuerySet[Repository]:
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

    def get_domains_by_ids(
        self,
        *ids: typing.List[ULID],
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ):
        """
        a quick way to get objects by ids
        """
        return self.get_objs(
            conditions={"pk__in": ids},
            order_by=order_by,
            for_update=for_update,
        )

    def construct_domain(self, **kwargs) -> Repository:
        return self.repository(**kwargs)

    @ensure_infra("persistence")
    async def get_domain(
        self, id: ULID, raise_exceptions: bool = False
    ) -> typing.Optional[Repository]:
        try:
            return await self.repository.from_id(id=id)
        except Exception as err:
            if raise_exceptions:
                raise err
            return None

    @ensure_infra("persistence")
    async def create_domain(
        self,
        **kwargs,
    ) -> Repository:
        """
        use create to insert domains quickly
        """
        return await self.repository.create(**kwargs)

    @ensure_infra("persistence")
    async def update_domain(
        self,
        *ids: typing.List[ULID],
        **kwargs,
    ) -> None:
        """
        use update to update domains
        """
        qs = self.get_objs_by_ids(*ids, for_update=True)
        await qs.update(**kwargs)

    @ensure_infra("persistence")
    async def bulk_create_domains(
        self,
        domains: typing.List[Repository],
    ):
        """
        use bulk create to insert domains quickly
        """
        await self.repository.bulk_create(domains)

    @ensure_infra("persistence")
    async def bulk_update_domains(
        self,
        domains: typing.List[Repository],
        update_fields: typing.List[str],
    ):
        """
        use bulk update to update domains quickly
        """
        await self.repository.bulk_update(domains, fields=update_fields)

    @ensure_infra("persistence")
    async def destory_domains(
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

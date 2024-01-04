# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from message import exceptions
from message import models
from message.applications.base import ApplicationBase
from message.helpers.decorators import ensure_infra
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from ulid import ULID


class ContactApplication(ApplicationBase[models.Contact]):
    def __init__(
        self, repository: typing.Type[models.Contact] = models.Contact
    ) -> None:
        self.repository = repository

    @ensure_infra("persistence")
    async def get_contacts(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> typing.AsyncIterable[models.Contact]:
        return await super().get_objs(
            conditions=conditions,
            offset=offset,
            limit=limit,
            order_by=order_by,
            for_update=for_update,
        )

    @ensure_infra("persistence")
    async def get_contact(self, id: ULID) -> typing.Optional[models.Contact]:
        return await super().get_obj(id)

    @ensure_infra("persistence")
    async def get_contact_by_code(self, code: str) -> typing.Optional[models.Contact]:
        return await self.repository.from_code(code=code)

    @ensure_infra("persistence")
    async def create_contact(
        self,
        name: str,
        code: str,
        definition: typing.Dict,
        description: typing.Optional[str] = None,
        from_api: bool = False,
    ) -> models.Contact:
        code = code.lower()
        if await self.repository.active_objects.filter(code=code).exists():
            raise exceptions.ContactDuplicatedCodeError
        validated = self.repository.definition_model.model_validate(
            definition,
            context={"from_api": from_api},
        )
        return await self.repository.create(
            name=name,
            code=code,
            definition=validated.model_dump(),
            description=description,
        )

    @ensure_infra("persistence")
    async def update_contact(
        self,
        contact: models.Contact,
        name: typing.Optional[str] = None,
        code: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        definition: typing.Optional[typing.Dict] = None,
    ) -> models.Contact:
        if name is not None:
            await contact.set_name(name, save=False)
        if code is not None:
            await contact.set_code(code, save=False)
        if description is not None:
            await contact.set_description(description, save=False)
        if definition is not None:
            await contact.set_definition(definition, save=False)
        await contact.save(
            update_fields=[
                "name",
                "code",
                "description",
                "definition",
                "updated_at",
            ]
        )
        return contact

    @ensure_infra("persistence")
    async def destroy_contacts(
        self, *ids: typing.List[ULID]
    ) -> typing.Literal["ok", "error"]:
        with suppress(Exception):
            async with in_transaction():
                await self.repository.active_objects.select_for_update().filter(
                    id__in=ids
                ).update(is_deleted=True, deleted_at=now())
                return "ok"
        return "error"

    @ensure_infra("persistence")
    async def update_contacts(
        self,
        contacts: typing.List[models.Contact],
        fields: typing.List[str],
        batch_size: typing.Optional[int] = None,
    ):
        await self.repository.bulk_update(
            contacts,
            fields=fields,
            batch_size=batch_size,
        )

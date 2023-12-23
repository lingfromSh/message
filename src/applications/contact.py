# Standard Library
import typing
from contextlib import suppress

# Third Party Library
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from ulid import ULID

# First Library
import exceptions
import models


class ContactApplication:
    def __init__(
        self, repository: typing.Type[models.Contact] = models.Contact
    ) -> None:
        self.repository = repository

    def get_contacts(
        self,
        conditions: typing.Dict = None,
        *,
        offset: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        order_by: typing.List[str] = None,
        for_update: bool = False,
    ) -> typing.AsyncIterable[models.Contact]:
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

    async def get_contact(self, contact_id: ULID) -> typing.Optional[models.Contact]:
        return await self.repository.from_id(id=contact_id)

    async def get_contact_by_code(self, code: str) -> typing.Optional[models.Contact]:
        return await self.repository.from_code(code=code)

    async def create_contact(
        self,
        name: str,
        code: str,
        definition: typing.Dict,
        description: typing.Optional[str] = None,
    ) -> models.Contact:
        if await self.repository.active_objects.filter(code=code).exists():
            raise exceptions.ContactDuplicatedCodeError
        validated = self.repository.definition_model.model_validate(definition)
        return await self.repository.create(
            name=name,
            code=code,
            definition=validated.model_dump(),
            description=description,
        )

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
        await contact.save(update_fields=["name", "code", "description", "definition"])
        return contact

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

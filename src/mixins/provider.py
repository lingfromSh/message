# Standard Library
import typing

# Third Party Library
from fastapi import status
from tortoise import Model
from tortoise.exceptions import MultipleObjectsReturned
from tortoise.transactions import atomic
from ulid import ULID

# First Library
import applications
import exceptions
import providers


class ProviderMixin:
    @classmethod
    async def from_id(cls, id: ULID) -> typing.Self:
        """
        Get user by id
        """
        domain = await cls.get_or_none(
            id=id,
            is_deleted=False,
            deleted_at__isnull=True,
        )
        if domain is None:
            raise exceptions.UserNotFoundError
        return domain

    @classmethod
    async def create_from_template(
        cls,
        code: str,
        *,
        name: str,
        description: typing.Optional[str] = None,
        params: typing.Optional[typing.Any] = None,
    ) -> typing.Self:
        """
        Create user from template
        """
        # First Library
        from providers.abc import __registry__

        application = applications.ContactApplication()

        if code not in __registry__:
            raise exceptions.ProviderCodeNotFoundError

        provider_cls = __registry__[code]
        provider_cls.validate_parameters(params)

        domain = await cls.create(
            name=name,
            code=code,
            description=description,
            params=params,
        )
        contacts = await application.get_contacts(
            conditions={"code__in": [provider_cls.supported_contacts]}
        )
        await domain.add_contacts(*contacts)
        return domain

    @property
    def repository(self) -> Model:
        return self.__class__

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    @atomic
    async def add_contacts(self, *contacts):
        """
        Add contacts to user
        """
        await self.contacts.add(*contacts)

    @atomic
    async def remove_contacts(self, *contacts, all: bool = False):
        """
        Remove contacts from user

        :param contacts: contacts to remove
        :param all: remove all contacts
        """
        if all is True:
            await self.contacts.clear()
        else:
            await self.contacts.remove(*contacts)

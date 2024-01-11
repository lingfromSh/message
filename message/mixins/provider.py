# Standard Library
import asyncio
import typing

# Third Party Library
from message import applications
from message import exceptions
from tortoise import Model
from tortoise.transactions import atomic
from ulid import ULID


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

        application = applications.ContactApplication()
        validated_params = cls.validate_params(
            provider_cls=cls.get_provider_cls(code),
            params=params,
        )

        domain = await cls.create(
            name=name,
            code=code,
            description=description,
            params=validated_params,
        )
        contact_qs = await application.get_contacts(
            conditions={
                "code__in": list(
                    map(
                        lambda e: e.value, cls.get_provider_cls(code).supported_contacts
                    )
                )
            }
        )
        await domain.add_contacts(*(await contact_qs))
        return domain

    @property
    def repository(self) -> Model:
        return self.__class__

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    @classmethod
    def get_provider_cls(cls, code: str):
        # Third Party Library
        from message.providers.abc import __registry__

        if code not in __registry__:
            raise exceptions.ProviderCodeNotFoundError
        return __registry__[code]

    @classmethod
    def get_provider_codes(cls):
        # Third Party Library
        from message.providers.abc import __registry__

        return list(__registry__.keys())

    @property
    def provider(self):
        return self.get_provider_cls(self.code)(parameters=self.params)

    @property
    def provider_cls(self):
        return self.get_provider_cls(self.code)

    @classmethod
    def validate_params(cls, provider_cls, params):
        validated = provider_cls.validate_parameters(params)
        if validated is not None:
            return validated.model_dump(exclude_none=True, exclude_defaults=True)
        return {}

    @atomic("default")
    async def add_contacts(self, *contacts):
        """
        Add contacts to user
        """
        await self.contacts.add(*contacts)

    @atomic("default")
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

    @atomic("default")
    async def set_name(self, name: str, save: bool = True):
        if save is True:
            await self.db.update(name=name)
        else:
            self.name = name

    @atomic("default")
    async def set_code(self, code: str, save: bool = True):
        if save is True:
            await self.db.update(code=code)
        else:
            self.code = code

    @atomic("default")
    async def set_description(self, description: str, save: bool = True):
        if save is True:
            await self.db.update(description=description)
        else:
            self.description = description

    @atomic("default")
    async def set_params(self, params: typing.Any, save: bool = True):
        validated = self.validate_params(
            provider_cls=self.provider_cls,
            params=params,
        )
        if save is True:
            await self.db.update(params=validated)
        else:
            self.params = validated

    async def send_message(self, message):
        """
        Send message to receivers

        return task id
        """

        await message.mark_as_scheduled()
        await message.mark_as_sending()
        await self.provider._send(message)
        await message.mark_as_succeeded()

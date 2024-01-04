# Standard Library
import typing

# Third Party Library
from message import exceptions
from ulid import ULID


class EndpointMixin:
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
            raise exceptions.EndpointNotFoundError
        return domain

    @property
    def repository(self) -> typing.Type[typing.Self]:
        return self.__class__.active_objects

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    async def check_contact_value(self, new_value) -> bool:
        validated_result = await (await self.contact).validate_contact(new_value)
        return validated_result

    async def set_value(self, value, *, save: bool = True):
        validated_result = await self.check_contact_value(value)
        if not validated_result.valid:
            raise exceptions.EndpointContactIsNotValidError
        if save:
            await self.db.update(value=validated_result.validated_data)
        else:
            self.value = validated_result.validated_data

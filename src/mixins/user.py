# Standard Library
import typing

# Third Party Library
from fastapi import status
from tortoise import Model
from tortoise.exceptions import MultipleObjectsReturned
from tortoise.transactions import atomic
from ulid import ULID

# First Library
import exceptions


class UserMixin:
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
    async def from_external_id(cls, external_id: str) -> typing.Self:
        """
        Get user by external id
        """
        try:
            domain = await cls.get_or_none(
                external_id=external_id,
                is_deleted=False,
                deleted_at__isnull=True,
            )
        except MultipleObjectsReturned:
            raise exceptions.UserDuplicatedExternalIDError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if domain is None:
            raise exceptions.UserNotFoundError
        return domain

    @property
    def repository(self) -> Model:
        return self.__class__

    @atomic
    async def activate(self, save: bool = True):
        """
        Activate user
        """
        if save:
            await self.repository.select_for_update().filter(id=self.id).update(
                is_active=True
            )
        else:
            self.is_active = True

    @atomic
    async def deactivate(self, save: bool = True):
        """
        Deactivate user
        """
        if save:
            await self.repository.select_for_update().filter(id=self.id).update(
                is_active=False
            )
        else:
            self.is_active = False

    @atomic
    async def set_external_id(self, external_id: str, save: bool = True):
        """
        Set external id
        """
        if await self.repository.filter(external_id=external_id).exists():
            raise exceptions.UserDuplicatedExternalIDError

        if save:
            await self.repository.select_for_update().filter(id=self.id).update(
                external_id=external_id
            )
        else:
            self.external_id = external_id

    @atomic
    async def set_metadata(self, metadata: typing.Dict, save: bool = True):
        """
        Set user metadata
        """
        if not isinstance(metadata, dict):
            raise exceptions.UserMetadataWithWrongTypeError

        if save:
            await self.repository.select_for_update().filter(id=self.id).update(
                metadata=metadata
            )
        else:
            self.metadata = metadata

    @atomic
    async def add_endpoints(self, *endpoints):
        """
        Add endpoints to user
        """
        await self.endpoints.add(*endpoints)

    @atomic
    async def remove_endpoints(self, *endpoints, all: bool = False):
        """
        Remove endpoints from user

        :param endpoints: endpoints to remove
        :param all: remove all endpoints
        """
        if all is True:
            await self.endpoints.clear()
        else:
            await self.endpoints.remove(*endpoints)

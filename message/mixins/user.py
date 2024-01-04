# Standard Library
import typing

# Third Party Library
from fastapi import status
from message import applications
from message import exceptions
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import RootModel
from pydantic import ValidationError
from pydantic import field_validator
from tortoise import Model
from tortoise.exceptions import MultipleObjectsReturned
from tortoise.transactions import atomic
from ulid import ULID


class UserEndpointAddInput(BaseModel):
    contact: typing.Union[str, ULID]
    value: typing.Any
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v):
        if isinstance(v, ULID):
            return v
        elif isinstance(v, str):
            return ULID.from_str(v)
        raise ValueError("Contact id must be ULID/ULID string")


class UserEndpointUpdateInput(BaseModel):
    id: typing.Union[str, ULID]
    value: typing.Any
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        if isinstance(v, ULID):
            return v
        elif isinstance(v, str):
            return ULID.from_str(v)
        raise ValueError("Contact id must be ULID/ULID string")


UserEndpointSetInput = RootModel[
    typing.Union[UserEndpointAddInput, UserEndpointUpdateInput]
]


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

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    @classmethod
    async def validate_external_id(cls, external_id, instance=None):
        qs = cls.filter(external_id=external_id)
        if instance is not None:
            qs = qs.exclude(id=instance.id)
        if await qs.exists():
            raise exceptions.UserDuplicatedExternalIDError
        return external_id

    @atomic("default")
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

    @atomic("default")
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

    @atomic("default")
    async def set_external_id(self, external_id: str, save: bool = True):
        """
        Set external id
        """
        external_id = await self.validate_external_id(external_id, instance=self)
        if save:
            await self.repository.select_for_update().filter(id=self.id).update(
                external_id=external_id
            )
        else:
            self.external_id = external_id

    @atomic("default")
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

    @atomic("default")
    async def add_endpoints(
        self,
        *endpoints: typing.List[typing.Dict],
    ):
        """
        Add endpoints to user

        endpoint must be dict
        """
        # TODO: optimize speed with bulk operations
        endpoint_application = applications.EndpointApplication()
        for endpoint in endpoints:
            try:
                endpoint = UserEndpointAddInput.model_validate(endpoint)
                await endpoint_application.create_endpoint(
                    user_id=self.id,
                    contact_id=endpoint.contact,
                    value=endpoint.value,
                )
            except ValidationError:
                raise exceptions.UserGotInvalidEndpointError

    @atomic("default")
    async def remove_endpoints(self, *endpoints, all: bool = False):
        """
        Remove endpoints from user

        :param endpoints: endpoints to remove
        :param all: remove all endpoints
        """
        application = applications.EndpointApplication()
        if all is True:
            endpoints = await application.get_endpoints_by_user_id(user_id=self.id)

        await application.destory_endpoints(*endpoints)

    @atomic("default")
    async def set_endpoints(self, *endpoints: typing.List[typing.Dict]):
        """
        Add new endpoints to user, keep existed, remove others
        """
        endpoint_application = applications.EndpointApplication()
        keep_endpoint_ids = []
        for endpoint in endpoints:
            try:
                endpoint = UserEndpointSetInput.model_validate(endpoint).root
                if isinstance(endpoint, UserEndpointAddInput):
                    endpoint_domain = await endpoint_application.create_endpoint(
                        user_id=self.id,
                        contact_id=endpoint.contact,
                        value=endpoint.value,
                    )
                    keep_endpoint_ids.append(endpoint_domain.id)
                elif isinstance(endpoint, UserEndpointUpdateInput):
                    # TODO: optimize speed with reducing db operations
                    endpoint_domain = await endpoint_application.get_endpoint(
                        id=endpoint.id,
                    )
                    await endpoint_application.update_endpoint(
                        endpoint=endpoint_domain,
                        value=endpoint.value,
                    )
                    # add id into keep list
                    keep_endpoint_ids.append(endpoint_domain.id)
                else:
                    # it should never happend
                    pass

            except ValidationError:
                raise exceptions.UserGotInvalidEndpointError
        need_destory_endpoints = (
            await endpoint_application.get_endpoints_by_user_id(user_id=self.id)
        ).exclude(id__in=keep_endpoint_ids)
        need_destory_endpoints = list(await need_destory_endpoints)
        return await endpoint_application.destory_endpoints(*need_destory_endpoints)

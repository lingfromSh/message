# Standard Library
import typing
from collections import namedtuple
from contextlib import suppress

# Third Party Library
import jsonschema
import pydantic
from pydantic import BaseModel
from pydantic import model_validator
from tortoise import Model
from tortoise.transactions import atomic
from ulid import ULID

# First Library
import exceptions
from common.constants import ContactEnum

ValidateResult = namedtuple("ValidateResult", ["valid", "validated_data"])


class ContactDefinitionModel(BaseModel):
    type: typing.Literal["jsonschema", "pydantic"] = "jsonschema"
    contact_schema: typing.Union[typing.Dict, str]

    def check_jsonschema(self):
        try:
            jsonschema.Validator.validate(self.contact_schema)
        except jsonschema.ValidationError:
            raise ValueError("Invalid JSON Schema")

    def check_pydantic_schema(self):
        if not self.get_pydantic_schema_model():
            raise ValueError("Pydantic schema not found")

    def get_pydantic_schema_model(self) -> typing.Optional[BaseModel]:
        return ContactMixin.get_schema(self.contact_schema)

    @model_validator(mode="after")
    def validate(self):
        if self.type == "jsonschema":
            self.check_jsonschema()
        elif self.type == "pydantic":
            self.check_pydantic_schema()
        return self

    def validate_contact(self, contact: typing.Any) -> ValidateResult:
        # REFRACTOR: more clear logic with one try-catch
        if self.type == "jsonschema":
            with suppress(jsonschema.ValidationError):
                jsonschema.validate(contact, self.contact_schema)
                return ValidateResult(True, contact)
        elif self.type == "pydantic":
            with suppress(pydantic.ValidationError):
                pydantic_schema_model = self.get_pydantic_schema_model()
                validated = pydantic_schema_model.model_validate(contact)
                return ValidateResult(True, validated)
        return ValidateResult(False, None)


class ContactMixin:
    definition_model = ContactDefinitionModel
    _contact_pydantic_models_ = {}

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
            raise exceptions.ContactNotFoundError
        return domain

    @classmethod
    async def from_code(cls, code: str) -> typing.Self:
        """
        Get user by code
        """
        domain = await cls.get_or_none(
            code=code,
            is_deleted=False,
            deleted_at__isnull=True,
        )
        if domain is None:
            raise exceptions.ContactNotFoundError
        return domain

    @classmethod
    def get_schemas(cls) -> typing.Dict:
        return cls._contact_pydantic_models_

    @classmethod
    def get_schema(
        cls,
        code: typing.Union[str, ContactEnum],
    ) -> typing.Optional[BaseModel]:
        try:
            code = ContactEnum(code)
            return cls._contact_pydantic_models_.get(code.value)
        except Exception:
            return

    @classmethod
    def register_schema(cls, code: ContactEnum, schema: BaseModel):
        if code in cls._contact_pydantic_models_:
            raise exceptions.ContactSchemaAlreadyRegisteredError
        cls._contact_pydantic_models_[code.value] = schema

    @property
    def repository(self) -> Model:
        return self.__class__

    @property
    def db(self):
        return self.repository.select_for_update().filter(id=self.id)

    @property
    def contact_schema(self) -> ContactDefinitionModel:
        return ContactDefinitionModel.model_validate(self.deifnition)

    @atomic
    async def set_definition(
        self, definition: typing.Dict[str, typing.Any], save: bool = True
    ):
        """
        Set definition
        """

        if save:
            await self.db.update(definition)
        else:
            self.deifnition = definition

    async def set_name(self, name: str, *, save: bool = True):
        """
        Set name
        """
        if save:
            await self.db.update(name=name)
        else:
            self.name = name

    async def set_code(self, code: str, *, save: bool = True):
        """
        Set code
        """
        if await self.db.select_for_update().filter(code=code).exists():
            raise exceptions.ContactDuplicatedCodeError
        if save:
            await self.db.update(code=code)
        else:
            self.code = code

    async def set_definition(self, definition: typing.Dict, *, save: bool = True):
        """
        Set definition
        """
        if save:
            await self.db.update(definition=definition)
        else:
            self.definition = definition

    async def set_description(self, description: typing.Dict, *, save: bool = True):
        """
        Set description
        """
        if save:
            await self.db.update(description=description)
        else:
            self.description = description

    async def validate_contact(self, contact: typing.Any) -> ValidateResult:
        with suppress(pydantic.ValidationError):
            validated = self.contact_schema.validate_contact(contact)
            return ValidateResult(True, validated)
        return ValidateResult(False, None)

# Standard Library
import enum
import re
import typing
from collections import namedtuple
from contextlib import suppress

# Third Party Library
import jsonschema
from message.exceptions.contact import ContactDuplicatedCodeError
from pydantic import BaseModel
from pydantic import ValidationInfo
from pydantic import field_validator
from pydantic import model_validator

ValidationResult = namedtuple("ValidationResult", ["valid", "validated_data"])


class ContactDefinitionModel(BaseModel):
    type: typing.Literal["jsonschema", "regex"] = "jsonschema"
    contact_schema: typing.Union[typing.Dict, str]

    def check_regex(self):
        try:
            re.compile(self.contact_schema)
        except re.error:
            raise ValueError("Invalid regex pattern")

    def check_jsonschema(self):
        # Do nothing, because jsonschema is flexible.
        # And user should check it by themselves.
        pass

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, value: str):
        if isinstance(value, enum.Enum):
            value = value.value
        return value

    @model_validator(mode="after")
    def validate(self, info: ValidationInfo):
        if self.type == "jsonschema":
            self.check_jsonschema()
        elif self.type == "regex":
            self.check_regex()
        return self

    def validate_contact(self, contact: typing.Any) -> ValidationResult:
        if self.type == "jsonschema":
            with suppress(jsonschema.ValidationError):
                jsonschema.validate(contact["jsonschema"], self.contact_schema)
                return ValidationResult(valid=True, validated_data=contact)
        elif self.type == "regex":
            if isinstance(contact, dict) and re.match(
                self.contact_schema, contact.get("regex", "")
            ):
                return ValidationResult(valid=True, validated_data=contact)
        return ValidationResult(valid=False, validated_data=None)


class ContactMixin:
    async def is_saved(self) -> bool:
        """
        Return True if the contact is saved in the database, False otherwise.
        """
        return self._saved_in_db

    async def validate(self, raise_exception: bool = False) -> bool:
        """
        Validate contact self

        Args:
            raise_exception (bool): Raise exception if validation failed.

        Returns:
            bool: True if the contact is valid, False otherwise.

        Raises:
            ValueError: If the contact definition is invalid.
        """
        try:
            ContactDefinitionModel.model_validate(self.definition)
            is_saved = await self.is_saved()
            qs = self.__class__.filter(code=self.code)
            if is_saved:
                qs = qs.exclude(id=self.id)
            if await qs.exists():
                raise ContactDuplicatedCodeError

            return True
        except Exception as error:
            # TODO: logging error
            if raise_exception:
                raise error
            return False

    def validate_endpoint_value(self, contact_value: str | dict) -> bool:
        """
        Validate the contact value according to the contact schema.

        Args:
            contact_value (str | dict): The contact value to be validated.

        Returns:
            bool: True if the contact value is valid, False otherwise.
        """
        definition_model = ContactDefinitionModel.model_validate(self.definition)
        validated_result = definition_model.validate_contact(contact_value)
        return validated_result.valid

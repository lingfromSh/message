# Third Party Library
from fastapi import status

# First Library
from exceptions.base import DefinedError

__all__ = [
    "ContactNotFoundError",
    "ContactSchemaAlreadyRegisteredError",
    "ContactDuplicatedCodeError",
]


class ContactNotFoundError(DefinedError):
    code = status.HTTP_404_NOT_FOUND
    status_code = status.HTTP_404_NOT_FOUND
    message = "Contact not found"


class ContactDuplicatedCodeError(DefinedError):
    message = "Contact with duplicated code already exists"


class ContactSchemaAlreadyRegisteredError(DefinedError):
    message = "Contact schema already registered"
# Third Party Library
from fastapi import status
from message.exceptions.base import DefinedError

__all__ = [
    "ContactNotFoundError",
    "ContactDuplicatedCodeError",
    "ContactValidationError",
    "ContactCannotDeleteBuiltinError",
    "ContactValidateMissingRequiredParamsError",
]


class ContactNotFoundError(DefinedError):
    code = status.HTTP_404_NOT_FOUND
    status_code = status.HTTP_404_NOT_FOUND
    message = "Contact not found"


class ContactDuplicatedCodeError(DefinedError):
    message = "Contact with duplicated code already exists"


class ContactValidationError(DefinedError):
    message = "Invalid contact"


class ContactCannotDeleteBuiltinError(DefinedError):
    message = "Cannot delete builtin contact"


class ContactValidateMissingRequiredParamsError(DefinedError):
    message = "Missing required parameters: {params}"

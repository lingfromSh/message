# Third Party Library
from fastapi import status

# First Library
from exceptions.base import DefinedError

__all__ = [
    "UserNotFoundError",
    "UserDuplicatedExternalIDError",
    "UserMetadataWithWrongTypeError",
]


class UserNotFoundError(DefinedError):
    code = status.HTTP_404_NOT_FOUND
    status_code = status.HTTP_404_NOT_FOUND
    message = "User not found"


class UserDuplicatedExternalIDError(DefinedError):
    message = "User has a duplicated external ID"


class UserMetadataWithWrongTypeError(DefinedError):
    message = "Metadata must be a map"

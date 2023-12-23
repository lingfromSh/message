# Standard Library
import typing

# Third Party Library
from fastapi import status


def get_class_attribute(
    cls, attribute_name: str, default: typing.Any = None
) -> typing.Any:
    """
    Get the attribute of a class.
    """
    return getattr(cls, attribute_name, default)


class DefinedError(Exception):
    """
    Defined Error
    """

    code: int = status.HTTP_400_BAD_REQUEST
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "some errors happended"
    details: typing.Optional[typing.Dict[str, typing.Any]] = None
    headers: typing.Optional[typing.Dict[str, str]] = None

    def __init__(
        self,
        message: typing.Optional[str] = None,
        *,
        status_code: typing.Optional[int] = None,
        code: typing.Optional[str] = None,
        details: typing.Optional[typing.Dict[str, typing.Any]] = None,
        headers: typing.Optional[typing.Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code or get_class_attribute(
            self.__class__,
            "status_code",
        )
        self.code = code or get_class_attribute(
            self.__class__,
            "code",
        )
        self.message = message or get_class_attribute(
            self.__class__,
            "message",
        )
        self.details = details or get_class_attribute(
            self.__class__,
            "details",
        )
        self.headers = headers or get_class_attribute(
            self.__class__,
            "headers",
        )

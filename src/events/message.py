# Standard Library
import typing

# Third Party Library
from pydantic import PlainSerializer
from pydantic import PlainValidator
from ulid import ULID as _ULID

# First Library
from events.base import EventSource

# Local Folder
from .base import SharedEvent
from .base import SimpleEvent


def validate_ulid(v: typing.Any) -> _ULID:
    if isinstance(v, _ULID):
        return v
    if isinstance(v, str):
        return _ULID.from_str(v)
    raise ValueError("invalid ulid")


def serialize_ulid(v: _ULID) -> str:
    return str(v)


ULID = typing.Annotated[
    typing.Union[str, _ULID],
    PlainValidator(validate_ulid),
    PlainSerializer(serialize_ulid, return_type=str),
]


class MessageBroadcastEvent(SharedEvent):
    _name: str = "message_broadcast"
    _fail_fast: bool = True

    provider_code: str
    message: typing.Any
    users: typing.List[ULID]
    endpoints: typing.List[ULID]
    contacts: typing.List[ULID]


class MessageSendEvent(SimpleEvent):
    _name: str = "message_send"
    _fail_fast: bool = True

    provider_code: str
    message: typing.Any
    users: typing.List[ULID]
    endpoints: typing.List[ULID]
    contacts: typing.List[ULID]

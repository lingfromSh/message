# Standard Library
import asyncio
import typing
from datetime import datetime

# Third Party Library
import orjson
import pendulum as pdl
from aio_pika.message import Message
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import conint
from pydantic import field_serializer
from pydantic import field_validator
from pydantic import model_validator
from pydantic.fields import PrivateAttr
from ulid import ULID

# First Library
from common.constants import QUEUE_NAME
from infra import get_infra

__registry__ = {}


def get_event_class(name: str) -> typing.Type["Event"]:
    return __registry__[name]


def generate_event_name() -> str:
    return "event-{}".format(ULID())


def make_event(event) -> "EventSource":
    event_source = EventSource.model_validate(
        dict(
            event_name=event._name,
            payload=event,
            retries=event._max_retries or 0,
        )
    )
    return event_source


class EventExecution(BaseModel):
    hostname: str
    pid: int
    tid: int
    executed_at: datetime = Field(default_factory=lambda: pdl.now(pdl.UTC))
    executed_cost: int = Field(default=0)
    status: typing.Literal["succeeded", "failed"]
    failed_reason: typing.Optional[str] = None
    return_value: typing.Optional[typing.Any] = None

    @field_serializer("return_value")
    @classmethod
    def serialize_return_value(cls, value: typing.Any) -> str:
        try:
            return orjson.dumps(value).decode()
        except orjson.JSONDecodeError:
            return str(value)
        except Exception:
            return "can not be serialized"


class EventSource(BaseModel):
    id: typing.Union[str, ULID] = Field(default_factory=ULID)
    event_name: str
    enqueued_at: datetime = Field(default_factory=lambda: pdl.now(pdl.UTC))
    payload: BaseModel

    retries: conint(gt=-1) = Field(default=0)
    retried: conint(gt=-1) = Field(default=0)
    executions: typing.List[EventExecution] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    @classmethod
    def validate_payload(cls, data):
        payload = data.get("payload")
        if isinstance(payload, BaseModel):
            return data
        event_class = get_event_class(data["event_name"])
        data["payload"] = event_class.model_validate_json(payload)
        return data

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: typing.Union[str, ULID]) -> ULID:
        if isinstance(v, str):
            return ULID.from_str(v)
        return v

    @field_serializer("id")
    def serialize_id(self, id: typing.Union[str, ULID]) -> str:
        return str(id)

    @field_serializer("payload")
    def serialize_payload(self, payload: BaseModel) -> str:
        return payload.model_dump_json()

    @computed_field
    @property
    def return_value(self) -> typing.Optional[typing.Any]:
        for execution in reversed(self.executions):
            ret_val = execution.return_value
            try:
                return orjson.loads(ret_val)
            except orjson.JSONDecodeError:
                return ret_val
        return None

    async def retry(self):
        await self.payload.retry()


class Event(BaseModel):
    # Private Attributes
    _name: str = PrivateAttr(default_factory=generate_event_name)
    _fail_fast: bool = False
    _max_retries: typing.Optional[int] = None
    _max_delay: typing.Optional[int] = None
    # TODO: impl result backend

    def __init_subclass__(cls, **kwargs):
        __registry__[cls._name.get_default()] = cls
        return super().__init_subclass__(**kwargs)

    async def emit(
        self,
        delay: typing.Optional[int] = None,
    ):
        raise NotImplementedError

    async def handle(self, event: typing.Self, event_source: EventSource):
        raise NotImplementedError


class SimpleEvent(Event):
    async def emit(
        self,
        delay: typing.Optional[int] = None,
    ):
        if delay is not None:
            await asyncio.sleep(delay)

        infra = get_infra()
        queue = await infra.queue()
        message = Message(body=make_event(self).model_dump_json())
        async with queue.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                message=message,
                routing_key=QUEUE_NAME,
            )


class SharedEvent(Event):
    async def emit(
        self,
        delay: typing.Optional[int] = None,
    ):
        if delay is not None:
            await asyncio.sleep(delay)

        infra = get_infra()
        cache = await infra.cache()

        await cache.redis.publish("shared_events", make_event(self).model_dump_json())

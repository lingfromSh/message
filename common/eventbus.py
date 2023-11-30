import inspect
from asyncio import Semaphore
from typing import List

from aio_pika.abc import AbstractIncomingMessage
from aio_pika.message import Message
from pydantic import BaseModel
from sanic import Sanic

from common.constants import TopicSubscriberType
from common.pubsub import TopicSubscriber
from utils import get_app

__events__ = {}
__event_handlers__ = {}

BaseEvent = BaseModel


class CannotResolveError(Exception):
    ...


app = get_app()


def event_handler(event_type: BaseEvent):
    """
    >>> from pydantic import BaseModel
    >>> from typing import Dict
    >>> class MessageCreateEvent(BaseModel):
    >>>     provider: Dict
    >>>     message: Dict
    >>>
    >>> @event_handler(MessageCreateEvent)
    >>> async def handle_message_create(event: MessageCreateEvent):
    >>>     ...
    """
    assert issubclass(event_type, BaseEvent)

    def to_message(self):
        return event_to_message(self)

    def wrapper(func):
        event_type.to_message = to_message
        __events__.update({make_event_id(event_type): event_type})
        __event_handlers__.setdefault(make_event_id(event_type), []).append(func)
        return func

    return wrapper


def make_event_id(event: BaseEvent):
    """
    return id of this event
    """
    if callable(event):
        return event.__name__.lower()
    else:
        return make_event_id(event.__class__)


def event_to_message(event: BaseEvent):
    """
    convert event to message
    """

    return Message(
        body=event.model_dump_json().encode(),
        headers={"event_id": make_event_id(event)},
    )


def get_event(event_id: str) -> BaseEvent | None:
    return __events__.get(event_id)


def get_handlers(event_id: str) -> List[callable] | None:
    return __event_handlers__.get(event_id)


class EventBusTopicSubscriber(TopicSubscriber):
    type = TopicSubscriberType.SHARED
    topic = "eventbus"
    durable = False
    deadletter = False

    @classmethod
    async def handle(
        cls,
        app: Sanic,
        message: AbstractIncomingMessage,
        semaphore: Semaphore = None,
        context: dict = ...,
    ):
        async with message.process():
            event_id = message.headers.get("event_id")
            event = get_event(event_id)
            handlers = get_handlers(event_id)

            if not handlers:
                # NOTE: event handlers not found, reject this message
                return

            if not event:
                # NOTE: event not found, reject this message
                return

            event = event.model_validate_json(message.body)
            for handler in handlers:
                try:
                    if inspect.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception:
                    ...

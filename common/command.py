from __future__ import annotations
import aio_pika
import sanic
import ulid
from functools import partial
from collections import OrderedDict
from sanic.log import logger
from common.constants import TOPIC_EXCHANGE_NAME
from common.exceptions import ImproperlyConfiguredException


__topic_subscirbers__ = OrderedDict()


def add_topic_subscriber(subscriber: TopicSubscriber):
    """
    Register topic subscriber
    """
    global __topic_subscirbers__
    if subscriber.topic in __topic_subscirbers__:
        raise ImproperlyConfiguredException("duplicated topic")
    __topic_subscirbers__.update({subscriber.topic, subscriber})


def remove_topic_subscriber(topic: str):
    """
    Unregister topic
    """
    global __topic_subscirbers__
    if topic not in __topic_subscirbers__:
        return
    return __topic_subscirbers__.pop(topic)


class TopicSubscriber:
    topic: str
    # default: True
    durable: bool | True

    def __init_subclass__(cls) -> None:
        topic = getattr(cls, "topic", None)
        if topic is None or not isinstance(topic, str):
            raise ImproperlyConfiguredException("invalid topic")
        cls.topic = topic.lower()

        durable = getattr(cls, "durable", True)
        cls.durable = durable

        add_topic_subscriber(cls)

    @classmethod
    def handle(cls, app: sanic.Sanic, message: aio_pika.abc.AbstractIncomingMessage):
        raise NotImplementedError


async def setup(app: sanic.Sanic, connection: aio_pika.abc.AbstractConnection) -> bool:
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange(
            TOPIC_EXCHANGE_NAME, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        for subscriber in __topic_subscirbers__.values():
            queue_name = f"message.topic.sub.{subscriber.topic}.queue"
            queue = await channel.declare_queue(name=queue_name, durable=True)
            await exchange.bind(
                exchange=aio_pika.ExchangeType.TOPIC, routing_key=queue.name
            )
            app.add_task(
                queue.consume(partial(subscriber.handle, app)),
                name=f"handle.{subscriber.topic}.task",
            )
        logger.info("setup topic subscribers")


def enrich(message: aio_pika.abc.AbstractMessage):
    """
    Give message id to message
    """
    if message.app_id is None:
        message.app_id = "message"
    if message.message_id is None:
        message.message_id = str(ulid.ULID())
    return message


async def publish(
    connection: aio_pika.abc.AbstractConnection,
    message: aio_pika.abc.AbstractMessage,
    topic: str = "*",
):
    """
    Publish command
    """

    async with connection.channel() as channel:
        exchange = await channel.get_exchange(name=TOPIC_EXCHANGE_NAME)

        await exchange.publish(enrich(message), routing_key=topic)
        logger.info(f"publish message {message.message_id} to {topic}")

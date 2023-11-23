from __future__ import annotations

import asyncio
from collections import OrderedDict
from datetime import timedelta
from functools import partial

import aio_pika
import sanic
import ulid
from pydantic import BaseModel
from sanic.log import logger

from common.constants import EXECUTOR_NAME
from common.constants import TOPIC_EXCHANGE_NAME
from common.exceptions import ImproperlyConfiguredException
from utils import get_app

__topic_subscirbers__ = OrderedDict()


def add_topic_subscriber(subscriber: TopicSubscriber):
    """
    Register topic subscriber
    """
    global __topic_subscirbers__
    if subscriber.topic in __topic_subscirbers__:
        raise ImproperlyConfiguredException("duplicated topic")
    __topic_subscirbers__.update({subscriber.topic: subscriber})


def remove_topic_subscriber(topic: str):
    """
    Unregister topic
    """
    global __topic_subscirbers__
    if topic not in __topic_subscirbers__:
        return
    return __topic_subscirbers__.pop(topic)


class TopicSubscriber:
    type: str = "broadcast"
    topic: str
    # default: True
    durable: bool = True
    # if deadletter is True, then create a deadletter. default: False
    deadletter: str = False
    message_model: BaseModel

    def __init_subclass__(cls) -> None:
        topic = getattr(cls, "topic", None)
        if topic is None or not isinstance(topic, str):
            raise ImproperlyConfiguredException("invalid topic")
        cls.topic = topic.lower()

        durable = getattr(cls, "durable", True)
        cls.durable = durable

        deadletter = getattr(cls, "deadletter", False)
        cls.deadletter = deadletter

        add_topic_subscriber(cls)

    @classmethod
    async def notify(cls, message: aio_pika.abc.AbstractMessage):
        await publish(message=message, topic=cls.topic)

    @classmethod
    async def delay_notify(
        cls, message: aio_pika.abc.AbstractMessage, delay: timedelta
    ):
        if not isinstance(delay, timedelta):
            delay = timedelta(seconds=int(delay))

        if delay.total_seconds() <= 0:
            await cls.notify(message)
        else:
            message.expiration = delay.total_seconds()
            await publish(message=message, topic=f"{cls.topic}.deadletter")

    @classmethod
    async def handle(
        cls,
        app: sanic.Sanic,
        message: aio_pika.abc.AbstractIncomingMessage,
        semaphore: asyncio.Semaphore = None,
        context: dict = {},
    ):
        raise NotImplementedError


__consumer_counter__ = {}

__counter__ = 0


def register_consumer(app, queue_name, subscriber):
    async def wrapped(max_workers: int = 1):
        global __consumer_counter__
        if __consumer_counter__.get(subscriber.topic, 0) >= max_workers:
            return

        if app.name != EXECUTOR_NAME:
            return

        async def func(app):
            queue = app.ctx.infra.queue()
            async with queue.channel_pool.acquire() as channel:
                queue: aio_pika.Queue = await channel.declare_queue(
                    queue_name, durable=subscriber.durable, auto_delete=True
                )
                try:
                    logger.debug(f"handle messages from {subscriber.topic}")
                    async with queue.iterator() as q:
                        async for m in q:
                            await subscriber.handle(app, m, context={})
                    logger.debug("finished handling messages")
                except aio_pika.exceptions.ChannelInvalidStateError:
                    logger.error(
                        f"consumer:{subscriber.topic} rpc timeout - reinsert consumer into loop"
                    )
                except Exception:
                    logger.exception(f"unexcepted error happend")

            __consumer_counter__[subscriber.topic] -= 1
            logger.debug(f"close consumer {subscriber.topic}")

        for _ in range(max_workers):
            __consumer_counter__[subscriber.topic] = (
                __consumer_counter__.get(subscriber.topic, 0) + 1
            )
            app.add_task(func)
        logger.debug(f"start new consumer {subscriber.topic}")

    app.ctx.task_scheduler.add_job(partial(wrapped, 10))


async def setup(app: sanic.Sanic, connection: aio_pika.abc.AbstractConnection) -> bool:
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange(
            TOPIC_EXCHANGE_NAME, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        for subscriber in __topic_subscirbers__.values():
            if subscriber.type == "broadcast":
                queue_name = f"message.topic.sub.{subscriber.topic}.queue.{app.ctx.worker_number}"
            else:
                queue_name = f"message.topic.sub.{subscriber.topic}.queue"
            queue = await channel.declare_queue(
                name=queue_name, durable=subscriber.durable, auto_delete=True
            )
            logger.debug(f"declare queue: {queue_name}")
            await queue.bind(exchange=exchange, routing_key=subscriber.topic)
            if subscriber.deadletter:
                deadletter_queue_name = (
                    f"message.topic.sub.{subscriber.topic}.deadletter.queue"
                )
                deadletter_queue = await channel.declare_queue(
                    name=deadletter_queue_name,
                    durable=subscriber.durable,
                    arguments={
                        "x-dead-letter-exchange": exchange.name,
                        "x-dead-letter-routing-key": subscriber.topic,
                    },
                )
                await deadletter_queue.bind(
                    exchange, routing_key=f"{subscriber.topic}.deadletter"
                )
            logger.debug(f"setup topic subscriber: {subscriber.topic}")
            register_consumer(app, queue_name, subscriber)


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
    message: aio_pika.abc.AbstractMessage,
    topic: str = "*",
):
    """
    Publish command
    """

    app = get_app()
    queue = app.ctx.infra.queue()
    async with queue.channel_pool.acquire() as channel:
        exchange = await channel.get_exchange(name=TOPIC_EXCHANGE_NAME)
        await exchange.publish(enrich(message), routing_key=topic)

from __future__ import annotations

import asyncio
import typing
from collections import OrderedDict
from datetime import timedelta
from functools import partial

import aio_pika
import sanic
import ulid
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel
from sanic.log import logger

from common.constants import EXECUTOR_NAME
from common.constants import TOPIC_EXCHANGE_NAME
from common.constants import TopicSubscriberType
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
    """
    topic subscriber

    type of topic subscriber
    broadcast or shared, broadcast use queue , shared use redis's pubsub
    default: broadcast
    """

    type: TopicSubscriberType = TopicSubscriberType.BROADCAST
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
    async def notify(cls, message: typing.Union[aio_pika.abc.AbstractMessage, bytes]):
        if cls.type == TopicSubscriberType.SHARED:
            assert isinstance(
                message, aio_pika.abc.AbstractMessage
            ), "shared task must send aio_pika.abc.AbstractMessage"
            await publish_shared_message(message=message, topic=cls.topic)
        else:
            assert isinstance(message, bytes), "broadcast task must send bytes"
            await published_broadcast_message(message=message, topic=cls.topic)

    @classmethod
    async def delay_notify(
        cls, message: aio_pika.abc.AbstractMessage, delay: timedelta
    ):
        assert (
            cls.type == TopicSubscriberType.SHARED
        ), "only shared task can send delay message"
        assert isinstance(
            message, aio_pika.abc.AbstractMessage
        ), "shared task must send aio_pika.abc.AbstractMessage"
        if not isinstance(delay, timedelta):
            delay = timedelta(seconds=int(delay))

        if delay.total_seconds() <= 0:
            await cls.notify(message)
        else:
            message.expiration = delay.total_seconds()
            await publish_shared_message(
                message=message, topic=f"{cls.topic}.deadletter"
            )

    @classmethod
    async def handle(
        cls,
        app: sanic.Sanic,
        message: bytes,
    ):
        raise NotImplementedError


__consumer_counter__ = {}


async def register_broadcast_task_consumer(app, subscriber):
    """
    register consumers of broadcast task

    Args:
        app: Sanic app
        subscriber: TopicSubscriber
    """

    async def start_consumer(max_workers):
        global __consumer_counter__
        if __consumer_counter__.get(subscriber.topic, 0) >= max_workers:
            return

        if app.name != EXECUTOR_NAME:
            return

        async def consume():
            # TODO: set an event to impl graceful shutdown
            try:
                async with app.ctx.infra.cache().pubsub() as pubsub:
                    await pubsub.subscribe(subscriber.topic)

                    while True:
                        message = await pubsub.get_message(
                            ignore_subscribe_messages=True
                        )
                        if message is None:
                            await asyncio.sleep(0)
                        else:
                            await subscriber.handle(app, message["data"])
            except Exception:
                pass

            __consumer_counter__[subscriber.topic] -= 1
            logger.debug(f"close consumer {subscriber.topic}")

        for _ in range(max_workers):
            __consumer_counter__[subscriber.topic] = (
                __consumer_counter__.get(subscriber.topic, 0) + 1
            )
            app.add_task(consume)

    app.ctx.task_scheduler.add_job(
        partial(start_consumer, 2), trigger=IntervalTrigger(seconds=5)
    )


async def register_shared_task_consumer(app, subscriber):
    """
    register consumers of shared task

    Args:
        app: Sanic app
        subscriber: TopicSubscriber
    """
    async with app.ctx.infra.queue().channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange(
            TOPIC_EXCHANGE_NAME, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
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

    async def start_consumer(max_workers: int = 1):
        """
        start consumer

        Args:
            max_workers:
        """
        global __consumer_counter__
        if __consumer_counter__.get(subscriber.topic, 0) >= max_workers:
            return

        if app.name != EXECUTOR_NAME:
            return

        async def consume(app):
            """
            consume messages

            Args:
                app: Sanic
            """
            queue = app.ctx.infra.queue()
            async with queue.channel_pool.acquire() as channel:
                queue: aio_pika.Queue = await channel.declare_queue(
                    queue_name, durable=subscriber.durable, auto_delete=True
                )
                try:
                    logger.debug(f"handle messages from {subscriber.topic}")
                    await queue.consume(partial(subscriber.handle, app))
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
            app.add_task(consume)

    app.ctx.task_scheduler.add_job(
        partial(start_consumer, 2), trigger=IntervalTrigger(seconds=5)
    )


async def setup_topic_subscribers(app: sanic.Sanic) -> bool:
    for subscriber in __topic_subscirbers__.values():
        if subscriber.type == TopicSubscriberType.BROADCAST:
            # register consumers for broadcast task
            await register_broadcast_task_consumer(app, subscriber)
        else:
            # register consumers for shared task
            await register_shared_task_consumer(app, subscriber)


def enrich(message: aio_pika.abc.AbstractMessage):
    """
    Give message id to message
    """
    if message.app_id is None:
        message.app_id = "message"
    if message.message_id is None:
        message.message_id = str(ulid.ULID())
    return message


async def publish_shared_message(
    message: aio_pika.abc.AbstractMessage,
    topic: str = "*",
):
    """
    Publish shared message to exchange
    """
    app = get_app()
    queue = app.ctx.infra.queue()
    async with queue.channel_pool.acquire() as channel:
        exchange = await channel.get_exchange(name=TOPIC_EXCHANGE_NAME)
        await exchange.publish(enrich(message), routing_key=topic)


async def published_broadcast_message(
    message: aio_pika.abc.AbstractMessage, topic: str
):
    """
    Publish broadcast message to redis
    """

    app = get_app()
    await app.ctx.infra.cache().publish(topic, message.body)

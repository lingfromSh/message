from __future__ import annotations

import asyncio
from collections import OrderedDict
from datetime import timedelta
from functools import partial

import aio_pika
import sanic
import ulid
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel
from sanic.log import logger

from common.constants import SERVER_NAME
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
    async def notify(cls, connection, message: aio_pika.abc.AbstractMessage):
        await publish(connection, message=message, topic=cls.topic)

    @classmethod
    async def delay_notify(
        cls, connection, message: aio_pika.abc.AbstractMessage, delay: timedelta
    ):
        if delay.total_seconds() <= 0:
            await cls.notify(connection, message)
        else:
            message.expiration = delay.total_seconds()
            await publish(connection, message=message, topic=f"{cls.topic}.deadletter")

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


def register_consumer(app, queue_name, subscriber):
    async def wrapped():
        global __consumer_counter__
        if __consumer_counter__.get(subscriber.topic, 0) != 0:
            return

        async def func():
            from apps.message.models import Provider
            from apps.scheduler.models import Plan

            async with app.ctx.queue.acquire() as connection:
                channel: aio_pika.Channel = await connection.channel()
                queue: aio_pika.Queue = await channel.declare_queue(
                    queue_name, durable=True
                )
                try:
                    context = {}
                    # context["providers"] = {p.pk: p async for p in Provider.find()}
                    # context["plans"] = {
                    #     p.pk: p async for p in Plan.find({"is_enabled": True})
                    # }
                    async for m in queue.iterator():
                        await subscriber.handle(app, m, context=context)
                    logger.info("finished handling messages")
                except aio_pika.exceptions.ChannelInvalidStateError:
                    logger.info(
                        f"consumer:{subscriber.topic} rpc timeout - reinsert consumer into loop"
                    )
                except Exception:
                    logger.exception(f"unexcepted error happend")

                # wait for consumer done
                await channel.close()

            __consumer_counter__[subscriber.topic] -= 1
            logger.info(f"close consumer {subscriber.topic}")

        __consumer_counter__[subscriber.topic] = 1
        logger.info(f"start new consumer {subscriber.topic}")
        await func()

    app.ctx.task_scheduler.add_job(wrapped)


async def setup(app: sanic.Sanic, connection: aio_pika.abc.AbstractConnection) -> bool:
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange(
            TOPIC_EXCHANGE_NAME, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        for subscriber in __topic_subscirbers__.values():
            if subscriber.type == "broadcast":
                queue_name = (
                    f"message.topic.sub.{subscriber.topic}.queue.{app.ctx.worker_id}"
                )
            else:
                queue_name = f"message.topic.sub.{subscriber.topic}.queue"
            queue = await channel.declare_queue(
                name=queue_name, durable=subscriber.durable
            )
            logger.info(f"declare queue: {queue_name}")
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
            logger.info(f"setup topic subscriber: {subscriber.topic}")
            if app.name == SERVER_NAME:
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

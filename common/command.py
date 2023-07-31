from __future__ import annotations

import asyncio
from collections import OrderedDict
from functools import partial
from contextlib import suppress
import async_timeout

import aio_pika
import sanic
import ulid
from apscheduler.triggers.interval import IntervalTrigger
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
    async def handle(
        cls,
        app: sanic.Sanic,
        semaphore: asyncio.Semaphore,
        message: aio_pika.abc.AbstractIncomingMessage,
    ):
        raise NotImplementedError


__consumer_counter__ = {}


def register_consumer(app, queue_name, subscriber):
    async def wrapped():
        global __consumer_counter__
        if __consumer_counter__.get(subscriber.topic, 0) != 0:
            return

        async def func():
            async with app.shared_ctx.queue.acquire() as connection:
                semaphore = asyncio.Semaphore()
                channel = await connection.channel()
                queue: aio_pika.Queue = await channel.declare_queue(
                    queue_name, durable=True
                )
                try:
                    await queue.consume(partial(subscriber.handle, app, semaphore))
                except aio_pika.exceptions.ChannelInvalidStateError:
                    logger.info(
                        f"consumer:{subscriber.topic} rpc timeout - reinsert consumer into loop"
                    )
                except Exception:
                    logger.exception(f"unexcepted error happend")

                # wait for consumer done
                await asyncio.sleep(1)
                await semaphore.acquire()
                await channel.close()
                semaphore.release()

            __consumer_counter__[subscriber.topic] -= 1
            logger.info(f"close consumer {subscriber.topic}")

        __consumer_counter__[subscriber.topic] = 1
        logger.info(f"start new consumer {subscriber.topic}")
        await func()

    app.shared_ctx.task_scheduler.add_job(wrapped, trigger=IntervalTrigger(seconds=2))


async def setup(app: sanic.Sanic, connection: aio_pika.abc.AbstractConnection) -> bool:
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange(
            TOPIC_EXCHANGE_NAME, type=aio_pika.ExchangeType.TOPIC, durable=True
        )
        for subscriber in __topic_subscirbers__.values():
            queue_name = f"message.topic.sub.{subscriber.topic}.queue"
            queue = await channel.declare_queue(name=queue_name, durable=True)
            await queue.bind(exchange=exchange, routing_key=subscriber.topic)
            logger.info(f"setup topic subscriber: {subscriber.topic}")
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

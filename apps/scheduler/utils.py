from sanic.log import logger
from datetime import UTC
from datetime import datetime

import orjson
from aio_pika import DeliveryMode
from aio_pika.message import Message

from apps.message.subscriber import InQueueMessageTopicSubscriber


async def publish_task(c, p, t=None):
    if t is None:
        t = datetime.now(tz=UTC)

    message = Message(
        body=orjson.dumps(
            InQueueMessageTopicSubscriber.message_model.model_validate(p).model_dump()
        ),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    await InQueueMessageTopicSubscriber.delay_notify(
        c,
        message=message,
        delay=(t - datetime.now(tz=UTC)).total_seconds(),
    )
    logger.info(f"Enqueue task {message.message_id}")

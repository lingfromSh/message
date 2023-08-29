from datetime import UTC
from datetime import datetime

from aio_pika import DeliveryMode
from aio_pika.message import Message

from apps.message.subscriber import InQueueMessageTopicSubscriber


async def publish_task(p, t=None):
    if t is None:
        t = datetime.now(tz=UTC)

    message = Message(
        body=InQueueMessageTopicSubscriber.message_model.model_validate(p)
        .model_dump_json()
        .encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    await InQueueMessageTopicSubscriber.delay_notify(
        message=message,
        delay=(t - datetime.now(tz=UTC)).total_seconds(),
    )

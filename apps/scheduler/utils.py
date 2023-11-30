from datetime import UTC
from datetime import datetime

from aio_pika import DeliveryMode
from aio_pika.message import Message

from apps.message.subscriber import InQueueBroadcastMessageTopicSubscriber
from apps.message.subscriber import InQueueMessageHandlerMixin
from apps.message.subscriber import InQueueSharedMessageTopicSubscriber


async def publish_task(p, broadcast=True, t=None):
    if t is None:
        t = datetime.now(tz=UTC)

    message = Message(
        body=InQueueMessageHandlerMixin.message_model.model_validate(p)
        .model_dump_json()
        .encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    if broadcast:
        subscriber = InQueueBroadcastMessageTopicSubscriber
    else:
        subscriber = InQueueSharedMessageTopicSubscriber

    await subscriber.delay_notify(
        message=message,
        delay=(t - datetime.now(tz=UTC)).total_seconds(),
    )

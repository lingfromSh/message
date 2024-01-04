# Third Party Library
import orjson
from aio_pika.message import Message
from ulid import ULID

# First Library
import applications
import models
from common.constants import QUEUE_NAME
from infra import get_infra


@models.Message.created.connect
async def on_message_created(sender):
    """
    Enqueue send task
    """
    infra = get_infra()
    queue_infra = await infra.queue()
    async with queue_infra.channel_pool.acquire() as channel:
        await channel.default_exchange.publish(
            message=Message(
                body=orjson.dumps(
                    {
                        "signal": "provider.new_message",
                        "data": {"message_id": str(sender.id)},
                    }
                )
            ),
            routing_key=QUEUE_NAME,
        )


@models.Provider.new_message.connect
async def on_new_message(sender, message_id):
    """
    Send message
    """
    message_application = applications.MessageApplication()
    message = await message_application.get_message(id=ULID.from_str(message_id))
    message.provider
    await message.provider.send_message(message)

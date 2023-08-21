import asyncio
from datetime import timedelta

import orjson
from aio_pika.message import Message
from sanic.log import logger

from apps.endpoint.subscriber import AddEndpointWebsocketTopicSubscriber
from apps.endpoint.subscriber import RemoveEndpointWebsocketTopicSubscriber
from utils import get_app

app = get_app()


async def register_websocket_endpoint(connection_id, data):
    try:
        data = orjson.loads(data)
    except orjson.JSONDecodeError:
        return

    if not isinstance(data, dict):
        return

    if "user_id" not in data:
        return

    external_id = data["user_id"]

    data = {"external_id": external_id, "connection_id": connection_id}

    async with app.ctx.queue.acquire() as connection:
        await AddEndpointWebsocketTopicSubscriber.delay_notify(
            connection,
            message=Message(body=orjson.dumps(data)),
            delay=timedelta(seconds=5),
        )


async def unregister_websocket_endpoint(connection_id):
    async with app.ctx.queue.acquire() as connection:
        await RemoveEndpointWebsocketTopicSubscriber.delay_notify(
            connection,
            message=Message(body=connection_id.encode()),
            delay=timedelta(seconds=30),
        )

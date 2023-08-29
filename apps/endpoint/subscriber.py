from __future__ import annotations

from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from asyncio import Semaphore
    from aio_pika.abc import AbstractIncomingMessage
    from sanic import Sanic

from sanic.log import logger

from apps.endpoint.models import Endpoint
from common.command import TopicSubscriber


class AddEndpointWebsocketTopicSubscriber(TopicSubscriber):
    type = "shared"
    topic = "add.endpoint.websocket"
    deadletter = True

    @classmethod
    async def handle(
        cls,
        app: Sanic,
        message: AbstractIncomingMessage,
        semaphore: Semaphore = None,
        context: dict = ...,
    ):
        cache = app.ctx.infra.cache()
        async with message.process(ignore_processed=True, requeue=True):
            try:
                data = orjson.loads(message.body)
            except Exception:
                return

            async def register(s):
                try:
                    endpoint = await Endpoint.find_one(
                        {"external_id": data["external_id"]}
                    )
                    websockets = set(endpoint.websockets)
                    websockets.add(data["connection_id"])
                    websockets = list(websockets)
                    await Endpoint.collection.update_one(
                        {"external_id": data["external_id"]},
                        {"$set": {"websockets": websockets}},
                        session=s,
                    )
                except Exception:
                    endpoint = Endpoint(
                        external_id=data["external_id"],
                        websockets=[data["connection_id"]],
                    )
                    await cache.set(
                        f"exid:{data['external_id']}:endpoint",
                        orjson.dumps(endpoint.dump()),
                    )
                    await Endpoint.collection.insert_one(endpoint.to_mongo(), session=s)

            async with cache.lock(f"modify.websocket.endpoint.connections", timeout=5):
                async with await app.ctx.db_client.start_session() as session:
                    await session.with_transaction(register)


class RemoveEndpointWebsocketTopicSubscriber(TopicSubscriber):
    type = "shared"
    topic = "remove.endpoint.websocket"
    deadletter = True

    @classmethod
    async def handle(
        cls,
        app: Sanic,
        message: AbstractIncomingMessage,
        semaphore: Semaphore = None,
        context: dict = ...,
    ):
        cache = app.ctx.infra.cache()

        async def unregister(s):
            modified_count = 0
            async for endpoint in Endpoint.find({"websockets": connection_id}):
                websockets = set(endpoint.websockets)
                websockets.remove(connection_id)
                websockets = list(websockets)
                await cache.set(
                    f"exid:{endpoint.external_id}:endpoint",
                    orjson.dumps(endpoint.dump()),
                )
                updated = await Endpoint.collection.update_one(
                    {"external_id": endpoint.external_id},
                    {"$set": {"websockets": websockets}},
                    session=s,
                )
                modified_count += updated.modified_count
                # logger.info(f"unregister websocket connection: {connection_id}")
            return modified_count

        async with message.process(ignore_processed=True, requeue=True):
            try:
                connection_id = message.body.decode()
            except Exception:
                await message.reject()

            async with cache.lock(f"modify.websocket.endpoint.connections", timeout=5):
                async with await app.ctx.db_client.start_session() as session:
                    modified_count = await session.with_transaction(unregister)

                    if modified_count == 0:
                        if not message.redelivered:
                            await message.reject(requeue=True)

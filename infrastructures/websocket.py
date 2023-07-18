import asyncio
from asyncio.queues import Queue
from asyncio.queues import QueueEmpty
from contextlib import suppress
from typing import Any

import async_timeout
from sanic.log import logger
from ulid import ULID
from websockets import exceptions as websockets_exceptions

from common.depend import Dependency


class WebsocketConnectionPoolDependency(
    Dependency, dependency_name="WebsocketPool", dependency_alias="ws_pool"
):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.connections = {}
        self.send_queues = {}
        self.recv_queues = {}
        self.listeners = {}

    def _gen_id(self) -> str:
        return str(ULID())

    def add_connection(self, connection) -> str:
        id = self._gen_id()
        self.connections[id] = connection
        self.send_queues[id] = Queue()
        self.app.add_task(
            self.send_task(self.send_queues[id], connection),
            name=f"websocket_{id}_send_task",
        )
        self.recv_queues[id] = Queue()
        self.app.add_task(
            self.recv_task(self.recv_queues[id], connection),
            name=f"websocket_{id}_recv_task",
        )
        self.app.add_task(self.notify_task(id), name=f"websocket_{id}_notify_task")
        self.app.add_task(self.is_alive_task(id), name=f"websocket_{id}_is_alive_task")
        setattr(connection, "_id", id)
        return connection._id

    def get_connection(self, connection_id: str):
        return self.connections.get(connection_id)

    def add_listener(self, connection_id, handler) -> str:
        id = self._gen_id()
        self.listeners.setdefault(connection_id, {}).update({id: handler})
        return id

    def remove_listener(self, connection_id, listener_id):
        self.listeners.get(connection_id, {}).pop(listener_id, None)

    def is_alive(self, connection_id: str):
        if hasattr(connection_id, "_id"):
            connection_id = connection_id._id
        return connection_id in self.connections

    async def remove_connection(self, connection: Any):
        if hasattr(connection, "_id"):
            connection_id = connection._id
        else:
            connection_id = connection

        if connection_id in self.send_queues:
            self.send_queues.pop(connection_id)

        if connection_id in self.recv_queues:
            self.recv_queues.pop(connection_id)

        if connection_id in self.listeners:
            self.listeners.pop(connection_id)

        if connection_id in self.connections:
            self.connections.pop(connection_id)

        await self.app.cancel_task(f"websocket_{connection_id}_send_task")
        await self.app.cancel_task(f"websocket_{connection_id}_recv_task")
        await self.app.cancel_task(f"websocket_{connection_id}_notify_task")
        await self.app.cancel_task(f"websocket_{connection_id}_is_alive_task")

    async def prepare(self):
        self.is_prepared = True
        logger.info("dependency:WebsocketPool is prepared")
        return self.is_prepared

    async def check(self):
        return True

    async def send_task(self, queue, connection):
        while self.is_alive(connection):
            try:
                data = queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(0)
                continue
            try:
                await connection.send(data)
                queue.task_done()
            except websockets_exceptions.ConnectionClosed:
                await self.remove_connection(connection)
            except Exception as err:
                logger.warning(str(err))
        else:
            await connection.close()

    async def recv_task(self, queue, connection):
        while self.is_alive(connection):
            try:
                await queue.put(await connection.recv())
            except websockets_exceptions.ConnectionClosed:
                await self.remove_connection(connection)
            except Exception as err:
                logger.warning(str(err))
        else:
            await connection.close()

    async def notify_task(self, connection_id):
        while connection_id in self.recv_queues:
            data = await self.recv_queues[connection_id].get()
            for listener in self.listeners.get(connection_id, {}).values():
                self.app.add_task(listener(data))

    async def is_alive_task(self, connection_id: str):
        if hasattr(connection_id, "_id"):
            connection_id = connection_id._id

        get_pong = asyncio.Event()

        async def wait_pong(data):
            if data != "pong":
                return
            get_pong.set()

        while True:
            get_pong.clear()
            await self.send(connection_id, "ping")
            listener_id = self.add_listener(connection_id, wait_pong)

            with suppress(asyncio.TimeoutError):
                async with async_timeout.timeout(
                    self.app.config.WEBSOCKET_PING_TIMEOUT
                ):
                    await get_pong.wait()
                    self.remove_listener(connection_id, listener_id)

            if not get_pong.is_set():
                await self.remove_connection(connection_id)
                break

            await asyncio.sleep(self.app.config.WEBSOCKET_PING_INTERVAL)

    async def wait_closed(self, connection_id: str):
        """
        if negative=True, only release when client close this connection.
        """
        while self.is_alive(connection_id):
            await asyncio.sleep(0)
        return False

    async def send(self, connection_id: str, data: Any):
        if not self.is_alive(connection_id):
            return
        if connection_id not in self.send_queues:
            return
        await self.send_queues[connection_id].put(data)

import asyncio
from asyncio.queues import Queue
from asyncio.queues import QueueEmpty
from contextlib import suppress
from typing import Any

import async_timeout
import orjson
from sanic.log import logger
from ulid import ULID

from common.depend import Dependency

PING = "#ping"
PONG = "#pong"


class WebsocketConnectionPoolDependency(
    Dependency, dependency_name="WebsocketPool", dependency_alias="ws_pool"
):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.lock = asyncio.Lock()
        self.connections = {}
        self.send_queues = {}
        self.recv_queues = {}
        self.close_callbacks = {}
        self.listeners = {}

    def _gen_id(self) -> str:
        return str(ULID())

    async def add_connection(self, connection) -> str:
        async with self.lock:
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
            self.app.add_task(
                self.is_alive_task(id), name=f"websocket_{id}_is_alive_task"
            )
            setattr(connection, "_id", id)
            return connection._id

    def get_connection(self, connection_id: str):
        return self.connections.get(connection_id)

    async def add_listener(self, connection_id, handler) -> str:
        async with self.lock:
            id = self._gen_id()
            self.listeners.setdefault(connection_id, {}).update({id: handler})
            return id

    async def remove_listener(self, connection_id, listener_id):
        async with self.lock:
            self.listeners.get(connection_id, {}).pop(listener_id, None)

    async def add_close_callback(self, connection_id, callback):
        async with self.lock:
            self.close_callbacks.setdefault(connection_id, []).append(callback)

    def is_alive(self, connection_id: str):
        if hasattr(connection_id, "_id"):
            connection_id = connection_id._id
        return connection_id in self.connections

    async def remove_connection(self, connection: Any):
        if hasattr(connection, "_id"):
            connection_id = connection._id
        else:
            connection_id = connection

            if connection_id not in self.connections:
                # removed already
                return

        async with self.lock:
            # logger.info(f"remove connection: {connection_id}")

            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_send_task")
            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_recv_task")
            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_notify_task")
            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_is_alive_task")

            if connection_id in self.send_queues:
                del self.send_queues[connection_id]

            if connection_id in self.recv_queues:
                del self.recv_queues[connection_id]

            if connection_id in self.listeners:
                del self.listeners[connection_id]

            if connection_id in self.close_callbacks:
                await self.do_close_callbacks(connection_id)
                del self.close_callbacks[connection_id]

            if connection_id in self.connections:
                del self.connections[connection_id]

    async def do_close_callbacks(self, connection_id):
        for cb in self.close_callbacks.get(connection_id, []):
            self.app.add_task(cb(connection_id))

    async def prepare(self):
        self.is_prepared = True
        # logger.info("dependency:WebsocketPool is prepared")
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
                if isinstance(data, (bytes, str, int)):
                    await connection.send(data)
                else:
                    await connection.send(orjson.dumps(data).decode())
                queue.task_done()
            except Exception as err:
                break

    async def recv_task(self, queue, connection):
        while self.is_alive(connection):
            try:
                data = await connection.recv()
                await queue.put(data)
                # logger.info(f"recv message: {data} from connection: {connection._id}")
            except Exception as err:
                break

    async def notify_task(self, connection_id):
        while self.is_alive(connection_id):
            try:
                # logger.info(f"notify connection: {connection_id}'s listeners")
                data = await self.recv_queues[connection_id].get()
                for listener in self.listeners.get(connection_id, {}).values():
                    await listener(connection_id, data)
            except Exception as err:
                pass

    async def is_alive_task(self, connection_id: str):
        if hasattr(connection_id, "_id"):
            connection_id = connection_id._id

        get_pong = asyncio.Event()

        async def wait_pong(connection_id, data):
            if data != PONG:
                return
            get_pong.set()

        while True:
            get_pong.clear()
            await self.send(connection_id, PING)
            listener_id = await self.add_listener(connection_id, wait_pong)

            with suppress(asyncio.TimeoutError):
                async with async_timeout.timeout(
                    self.app.config.WEBSOCKET_PING_TIMEOUT
                ):
                    await get_pong.wait()

            await self.remove_listener(connection_id, listener_id)
            if get_pong.is_set():
                # this connection is closed
                await asyncio.sleep(self.app.config.WEBSOCKET_PING_INTERVAL)
            else:
                await self.remove_connection(connection_id)

    async def wait_closed(self, connection_id: str):
        """
        if negative=True, only release when client close this connection.
        """
        while self.is_alive(connection_id):
            await asyncio.sleep(0)
        return False

    async def send(self, connection_id: str, data: Any) -> bool:
        if not self.is_alive(connection_id):
            return False
        if connection_id not in self.send_queues:
            return False
        await self.send_queues[connection_id].put(data)

        return True

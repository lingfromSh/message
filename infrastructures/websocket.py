import asyncio
from asyncio.queues import Queue
from asyncio.queues import QueueEmpty
from contextlib import suppress
from typing import Any

import orjson
from sanic.exceptions import WebsocketClosed
from sanic.log import logger
from ulid import ULID


class WebsocketPoolDependency:
    def __init__(self, app) -> None:
        self.app = app
        self.lock = asyncio.Lock()
        self.connections = {}
        self.send_queues = {}
        self.recv_queues = {}
        self.close_callbacks = {}
        self.listeners = {}
        logger.debug("dependency: websocket pool is configured")

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
            logger.debug(f"remove connection: {connection_id}")

            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_send_task")
            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_recv_task")
            with suppress(Exception):
                await self.app.cancel_task(f"websocket_{connection_id}_notify_task")

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

            # remove cancelled tasks and completed tasks
            self.app.purge_tasks()

    async def do_close_callbacks(self, connection_id):
        for cb in self.close_callbacks.get(connection_id, []):
            self.app.add_task(cb(connection_id))

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
                logger.debug(f"send message: {data} to connection: {connection._id}")
            except WebsocketClosed:
                break
            except Exception as err:
                logger.exception(f"failed to send task: {err}")
                break

    async def recv_task(self, queue, connection):
        while self.is_alive(connection):
            try:
                data = await connection.recv()
                logger.debug(f"recv message: {data} from connection: {connection._id}")
                await queue.put(data)
            except WebsocketClosed:
                break
            except Exception as err:
                logger.exception(
                    f"failed to recv task for connection[{connection._id}]: {err}"
                )
                break

    async def notify_task(self, connection_id):
        while self.is_alive(connection_id):
            try:
                logger.debug(f"notify connection: {connection_id}")
                data = await self.recv_queues[connection_id].get()
                for listener in self.listeners.get(connection_id, {}).values():
                    await listener(connection_id, data)
            except WebsocketClosed:
                break
            except Exception as err:
                logger.exception(f"failed to notify connection[{connection_id}]: {err}")
                break

    async def wait_closed(self, connection_id: str):
        """
        only release when this connection lost
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

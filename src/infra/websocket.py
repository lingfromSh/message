# Standard Library
import asyncio
import typing
from asyncio.queues import Queue
from contextlib import suppress

# Third Party Library
import backoff
import orjson
from fastapi import WebSocket
from ulid import ULID

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus
from infra.abc import Infrastructure


async def print_close_connection_id(id):
    ...


class WebsocketConnection:
    TERMINATE = "terminate#"

    def __init__(
        self,
        id,
        websocket: WebSocket,
        background_scheduler,
        *,
        listeners: typing.List[typing.Callable] = None,
        close_callbacks: typing.List[typing.Callable] = None,
    ):
        self.id = id
        self.websocket = websocket
        self.background_scheduler = background_scheduler
        self.recv_task: asyncio.Task = None
        self.recv_queue = Queue()
        self.listeners = listeners if listeners else []
        self.close_callbacks = close_callbacks if close_callbacks else []
        self.close_event = asyncio.Event()

    async def send(self, message):
        try:
            message = orjson.dumps(message).decode()
            send_method = self.websocket.send_text
        except orjson.JSONDecodeError:
            message = message
            send_method = self.websocket.send_json

        with suppress(BaseException):
            await send_method(message)

    async def notify(self, data):
        for listener in self.listeners:
            try:
                await listener(self, data)
            except BaseException:
                pass

    async def start_notify_task(self):
        async def task():
            while True:
                data = await self.recv_queue.get()
                if data == self.TERMINATE:
                    break
                await self.notify(data)

        self.recv_task = asyncio.create_task(task())

    async def keep_alive(self):
        async for data in self.websocket.iter_text():
            try:
                data = orjson.loads(data)
            except orjson.JSONDecodeError:
                pass
            try:
                await self.recv_queue.put(data)
            except Exception as e:
                print(e)
        self.close_event.set()

    async def send_welcome(self):
        await self.send({"type": "welcome", "id": self.id})

    async def init(self):
        await self.websocket.accept()
        await self.start_notify_task()

    async def shutdown(self) -> bool:
        for close_callback in self.close_callbacks:
            self.background_scheduler.run_task_in_process_executor(
                close_callback,
                args=(self.id,),
            )
        self.close_event.set()
        await self.recv_queue.put(self.TERMINATE)
        return self.recv_task.done() and await self.close_event.wait()

    def __del__(self):
        del self.id
        del self.websocket
        del self.recv_task
        del self.recv_queue
        del self.close_event
        del self.listeners


class WebsocketInfrastructure(Infrastructure):
    def __init__(self):
        self.write_lock = asyncio.Lock()
        self.connections = {}

    def generate_id(self) -> ULID:
        generated = str(ULID())
        while generated in self.connections:
            generated = str(ULID())
        return generated

    async def health_check(self) -> HealthStatus:
        return HealthStatus(
            status="up",
            checks=[
                CheckResult(
                    check="init check",
                    status="up",
                    result="inited",
                )
            ],
        )

    async def init(self, background_scheduler) -> Infrastructure:
        self.background_scheduler = background_scheduler
        return self

    async def shutdown(self, resource: Infrastructure):
        for connection in self.connections.values():
            await connection.shutdown()
        self.connections.clear()

    async def add_connection(self, connection: WebSocket) -> WebsocketConnection:
        """
        add connection to connections
        """
        # TODO: add some background tasks
        connection_id = self.generate_id()
        try:
            async with self.write_lock:
                self.connections[connection_id] = WebsocketConnection(
                    connection_id,
                    connection,
                    self.background_scheduler,
                )
        except Exception as e:
            print(e)
        return self.connections[connection_id]

    async def remove_connection(self, connection: WebsocketConnection):
        await connection.shutdown()
        del self.connections[connection.id]
        del connection

    async def send(self, message, connection_ids) -> typing.List[bool]:
        results = []
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send(message)
                    results.append(True)
                except Exception as err:
                    results.append(False)
            else:
                results.append(False)

        return results

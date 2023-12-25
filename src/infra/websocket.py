# Standard Library
import asyncio
import typing
from asyncio.queues import Queue
from weakref import WeakValueDictionary

# Third Party Library
import orjson
from fastapi import WebSocket
from ulid import ULID

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus
from infra.abc import Infrastructure


class WebsocketConnection:
    TERMINATE = "terminateterminateterminate"

    def __init__(
        self,
        id,
        websocket: WebSocket,
        *,
        listeners: typing.List[typing.Callable] = None
    ):
        self.id = id
        self.websocket = websocket
        self.recv_task = None
        self.keep_alive_task = None
        self.recv_queue = Queue()
        self.listeners = listeners
        self.close_event = asyncio.Event()

    async def send(self, message):
        try:
            await self.websocket.send_text(orjson.dumps(message).decode())
        except orjson.JSONDecodeError:
            await self.websocket.send_json(message)

    async def notify(self, data):
        for listener in self.listeners:
            try:
                await listener(self, data)
            except BaseException:
                pass

    async def start_recv_task(self):
        async def task(event):
            while True:
                data = await self.recv_queue.get()
                if data == self.TERMINATE:
                    break
                await self.notify(data)

        self.recv_task = asyncio.create_task(task(self.close_event))

    async def keep_alive(self):
        async def task(event):
            await event()
            self.recv_queue.put_nowait(self.TERMINATE)

        self.keep_alive_task = asyncio.create_task(task(self.close_event))

    async def init(self):
        await self.websocket.accept()
        await self.start_recv_task()
        await self.start_keep_alive()

    async def shutdown(self):
        await self.websocket.close()


class WebsocketInfrastructure(Infrastructure):
    def __init__(self):
        self.connections = WeakValueDictionary()

    def generate_id(self) -> ULID:
        return str(ULID())

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

    async def init(self) -> Infrastructure:
        return self

    async def shutdown(self, resource: Infrastructure):
        self.connections.clear()

    async def add_connection(self, connection: WebSocket) -> str:
        """
        add connection to connections
        """
        connection_id = self.generate_id()
        while connection_id in self.connections:
            connection_id = self.generate_id()
        self.connections[connection_id] = connection
        # TODO: add some background tasks
        return connection_id

    async def send(self, message, connection_ids):
        try:
            for connection_id in connection_ids:
                connection = self.connections.get(connection_id)
                if connection:
                    if isinstance(message, (str, int, float, bool)):
                        await connection.send_text(message)
                    else:
                        await connection.send_json(message)
            return True
        except Exception:
            return False

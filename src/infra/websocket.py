# Standard Library
import asyncio
import typing
from asyncio.queues import Queue

# Third Party Library
import backoff
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
        listeners: typing.List[typing.Callable] = None,
    ):
        self.id = id
        self.websocket = websocket
        self.recv_task = None
        self.recv_queue = Queue()
        self.listeners = listeners if listeners else []
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
        await self.websocket.send_json({"type": "welcome", "id": self.id})

    async def init(self):
        await self.websocket.accept()
        await self.start_recv_task()

    @backoff.on_predicate(
        backoff.expo,
        lambda x: x is True,
        max_tries=10,
    )
    async def shutdown(self) -> bool:
        self.close_event.set()
        self.recv_queue.put_nowait(self.TERMINATE)
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
        return "1"
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
        for connection in self.connections.values():
            await connection.shutdown()
        self.connections.clear()

    async def add_connection(self, connection: WebSocket) -> WebsocketConnection:
        """
        add connection to connections
        """
        # TODO: add some background tasks
        connection_id = self.generate_id()
        while connection_id in self.connections:
            connection_id = self.generate_id()
        try:
            async with self.write_lock:
                self.connections[connection_id] = WebsocketConnection(
                    connection_id, connection
                )
        except Exception as e:
            print(e)
        return self.connections[connection_id]

    async def remove_connection(self, connection: WebsocketConnection):
        await connection.shutdown()
        del self.connections[connection.id]
        del connection

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

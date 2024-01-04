# Standard Library
import asyncio
import typing
from asyncio.queues import Queue
from contextlib import suppress

# Third Party Library
import backoff
import orjson
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from message.infra.abc import CheckResult
from message.infra.abc import HealthStatus
from message.infra.abc import Infrastructure
from ulid import ULID


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
        if isinstance(message, (str, int, float, bool)):
            send_method = self.websocket.send_text
        elif isinstance(message, bytes):
            send_method = self.websocket.send_bytes
        else:
            try:
                message = orjson.dumps(message).decode()
                send_method = self.websocket.send_text
            except orjson.JSONDecodeError:
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
        with suppress(WebSocketDisconnect):
            async for data in self.websocket.iter_text():
                try:
                    data = orjson.loads(data)
                except orjson.JSONDecodeError:
                    pass
                try:
                    await self.recv_queue.put(data)
                except Exception as e:
                    print(e)

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
        return await self.close_event.wait() and self.recv_task.done()

    def __del__(self):
        del self.id
        del self.websocket
        del self.recv_task
        del self.recv_queue
        del self.close_event
        del self.listeners


class WebsocketInfrastructure(Infrastructure):
    TERMINATE = "terminate#"
    REMOTE_CHANNEL = "websocketremote_channel#"

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

    async def start_listen_remote_message(self):
        async for message in await self.distribution.subscribe(self.REMOTE_CHANNEL):
            if message["type"] == "message":
                data = message["data"]
                try:
                    data = orjson.loads(data)
                    if data["sender"] == self.id:
                        continue
                    await self.local_send(
                        data["message"],
                        connection_ids=data["connection_ids"],
                    )
                except Exception as err:
                    print(err)

    async def init(self, background_scheduler, distribution) -> Infrastructure:
        self.id = str(ULID())
        self.background_scheduler = background_scheduler
        self.distribution = distribution
        self.background_task = asyncio.create_task(self.start_listen_remote_message())
        return self

    async def shutdown(self, resource: Infrastructure):
        self.background_task.cancel()
        for connection in self.connections.values():
            await connection.shutdown()
        self.connections.clear()

    async def add_connection(self, connection: WebSocket) -> WebsocketConnection:
        """
        add connection to connections
        """
        # TODO: add some background tasks
        await increase_connection_count()
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
        await decrease_connection_count()
        await connection.shutdown()
        del self.connections[connection.id]
        del connection

    async def local_send(self, message, connection_ids) -> typing.List[bool]:
        ret = []
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if connection:
                try:
                    await connection.send(message)
                    ret.append(True)
                except Exception as err:
                    ret.append(False)
            else:
                ret.append(False)
        return ret

    async def remote_send(self, message, connection_ids) -> typing.List[bool]:
        data = {"sender": self.id, "message": message, "connection_ids": connection_ids}
        await self.distribution.publish(self.REMOTE_CHANNEL, data)

    async def send(self, message, connection_ids) -> typing.List[bool]:
        reachable = list(filter(lambda x: x in self.connections, connection_ids))
        unreachable = list(filter(lambda x: x not in self.connections, connection_ids))
        results = []

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.local_send(message, reachable))
            tg.create_task(self.remote_send(message, unreachable))

        return results

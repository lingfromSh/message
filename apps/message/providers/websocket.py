from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel

from apps.message.common.constants import MessageProviderType
from apps.message.providers.base import MessageProviderModel
from utils import get_app


class WebsocketMessageProviderModel(MessageProviderModel):
    class Info:
        name = "Websocket"
        description = "Bio-Channel Communication"
        type = MessageProviderType.WEBSOCKET

    class Capability:
        is_enabled = True
        can_send = True

    class Message(BaseModel):
        connections: List[str]
        action: str
        payload: Union[List, Dict, str, bytes]

    async def send(self, message: Message):
        app = get_app()
        websocket_pool = app.ctx.ws_pool

        for connection in message.connections:
            await websocket_pool.send(
                connection, data={"action": message.action, "payload": message.payload}
            )

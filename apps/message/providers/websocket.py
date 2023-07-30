from typing import Dict
from typing import List
from typing import Union

from sanic.log import logger
from pydantic import BaseModel

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.common.interfaces import SendResult
from apps.message.models import Message as MessageModel
from apps.message.providers.base import MessageProviderModel
from utils import get_app


class WebsocketMessageProviderModel(MessageProviderModel):
    class Info:
        name = "websocket"
        description = "Bio-Channel Communication"
        type = MessageProviderType.WEBSOCKET

    class Capability:
        is_enabled = True
        can_send = True

    class Message(BaseModel):
        connections: List[str]
        action: str
        payload: Union[List, Dict, str, bytes]

    async def send(self, provider_id, message: Message) -> SendResult:
        app = get_app()
        websocket_pool = app.ctx.ws_pool
        for connection in message.connections:
            await websocket_pool.send(
                connection, data={"action": message.action, "payload": message.payload}
            )

        return SendResult(
            provider_id=provider_id, message=message, status=MessageStatus.SUCCEEDED
        )

from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel
from sanic.log import logger

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
        logger.info(f"sending websocket message:{message}")
        app = get_app()
        websocket_pool = app.ctx.ws_pool

        sent_list = set()
        for connection in message.connections:
            sent = await websocket_pool.send(
                connection, data={"action": message.action, "payload": message.payload}
            )
            if not sent:
                continue
            sent_list.add(connection)

        if sent_list:
            return SendResult(
                provider_id=provider_id, message=message, status=MessageStatus.SUCCEEDED
            )

        return SendResult(
            provider_id=provider_id, message=message, status=MessageStatus.FAILED
        )

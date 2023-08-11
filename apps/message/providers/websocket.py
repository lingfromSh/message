from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel
from pydantic import field_serializer
from sanic.log import logger

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.common.interfaces import SendResult
from apps.message.providers.base import MessageProviderModel
from apps.message.validators.types import EndpointExID
from apps.message.validators.types import EndpointTag
from apps.message.validators.types import ETag
from apps.message.validators.types import ExID
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
        connections: List[Union[EndpointTag, EndpointExID, str]]
        action: str
        payload: Union[List, Dict, str, bytes]

        @field_serializer("connections")
        def serialize_connections(self, connections):
            return list(set(map(str, connections)))

    async def send(self, provider_id, message: Message) -> SendResult:
        logger.info(f"sending websocket message:{message}")
        app = get_app()
        websocket_pool = app.ctx.ws_pool

        sent_list = set()

        connections = []
        for connection in message.connections:
            if isinstance(connection, ETag):
                connections.extend(
                    [
                        w
                        for c in await connection.decode()
                        for w in c.websockets
                        if hasattr(c, "websockets")
                    ]
                )
            elif isinstance(connection, ExID):
                endpoint = await connection.decode()
                if endpoint:
                    connections.extend(endpoint.websockets)
            else:
                connections.append(connection)

        connections = list(set(filter(lambda x: x, connections)))

        for connection in connections:
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

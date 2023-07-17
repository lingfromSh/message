from typing import Union, List, Dict, ByteString
from pydantic import BaseModel
from apps.message.providers.base import MessageProviderModel
from apps.message.common.constants import MessageProviderType


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
        payload: Union[List, Dict, ByteString]

    async def send(self, message: Message):
        ...

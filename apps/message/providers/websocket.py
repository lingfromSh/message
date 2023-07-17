from typing import ByteString
from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel

from apps.message.common.constants import MessageProviderType
from apps.message.providers.base import MessageProviderModel


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

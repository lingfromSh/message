# Standard Library
import typing

# Third Party Library
from pydantic import RootModel
from ulid import ULID

# First Library
import applications
from common.constants import ContactEnum

# Local Folder
from .abc import ProviderBase

WebsocketMessageDefinition = RootModel[
    typing.Union[
        str,
        int,
        bool,
        float,
        list,
        dict,
    ]
]


class WebsocketProvider(ProviderBase):
    name: str = "websocket"
    description = "websocket provider"
    supported_contacts = [ContactEnum.WEBSOCKET]

    # ability
    can_send = True

    # no need to configure parameters
    parameter_definition = None
    message_definition: WebsocketMessageDefinition = WebsocketMessageDefinition

    async def send(self, message):
        validated = self.message_definition.model_validate_json(message.content).root
        connection_ids = message.contacts
        websocket = await self.infra.websocket()
        results = await websocket.send(validated, connection_ids=connection_ids)
        # TODO: user map, endpoint map, contact map
        return dict(zip(connection_ids, results))

# Standard Library
import typing

# Third Party Library
from pydantic import RootModel

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

    # ability
    can_send = True

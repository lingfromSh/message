# Standard Library
import typing

# Third Party Library
from pydantic import RootModel

# First Library
import applications
from common.constants import ContactEnum

# Local Folder
from .abc import ProviderBase


class WebsocketProvider(ProviderBase):
    name: str = "websocket"
    description = "websocket provider"
    supported_contacts = [ContactEnum.WEBSOCKET]

    # no need to configure parameters
    parameter_definition = None
    message_definition = RootModel[
        typing.Union[
            str,
            int,
            bool,
            float,
            list,
            dict,
        ]
    ]

    async def send(
        self,
        message: message_definition,
        *,
        users: typing.List[typing.Any] = None,
        endpoints: typing.List[typing.Any] = None,
        background: bool = True
    ):
        # TODO: endpoints must be type of Endpoint
        websocket = self.infra.websocket()
        application = applications.EndpointApplication()
        endpoints = await application.get_endpoints(
            conditions={
                "user_id__in": [user.id for user in users],
                "contact__code__in": self.supported_contacts,
            }
        ).values_list("value", flat=True)
        await websocket.send(message, connection_ids=endpoints)
        # TODO: record sent message

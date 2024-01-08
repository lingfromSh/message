# Standard Library
import typing

# Third Party Library
from message import applications
from message.common.constants import ContactEnum
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
    supported_contacts = [ContactEnum.WEBSOCKET]

    # ability
    can_send = True

    # no need to configure parameters
    parameter_definition = None
    message_definition: WebsocketMessageDefinition = WebsocketMessageDefinition

    async def send(self, message):
        validated = self.message_definition.model_validate_json(message.content).root
        connection_ids = [contact["connection"] for contact in message.contacts] or []
        endpoint_application = applications.EndpointApplication()
        async for endpoint in (
            await endpoint_application.get_endpoints(
                conditions={
                    "user_id__in": (
                        await message.end_users.all().values_list("id", flat=True)
                    ),
                }
            )
        ).prefetch_related("contact"):
            validated_contact = await endpoint.contact.validate_contact(endpoint.value)
            if validated_contact.valid:
                connection_ids.append(validated_contact.validated_data["connection"])

        async for endpoint in message.endpoints.filter(
            contact__code__in=self.supported_contacts
        ).prefetch_related("contact"):
            validated_contact = await endpoint.contact.validate_contact(endpoint.value)
            if validated_contact.valid:
                connection_ids.append(validated_contact.validated_data["connection"])
        websocket = await self.infra.websocket()
        results = await websocket.send(validated, connection_ids=connection_ids)
        return dict(zip(connection_ids, results))

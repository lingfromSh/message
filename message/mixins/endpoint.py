# Third Party Library
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from message.wiring import ApplicationContainer


class EndpointMixin:
    @inject
    async def validate(
        self, contact_application: Provide[ApplicationContainer.contact_application]
    ) -> bool:
        """
        Validate the endpoint value via contact.
        """
        return await contact_application.validate_contact_value(self.value)

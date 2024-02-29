# Third Party Library
from message.exceptions.endpoint import EndpointContactRequiredError
from message.exceptions.endpoint import EndpointInvalidValueError
from message.wiring import ApplicationContainer
from tortoise.queryset import QuerySet


class EndpointMixin:
    async def validate(self, raise_exception: bool = False) -> bool:
        """
        Validate the endpoint value via contact.
        """
        contact_application = ApplicationContainer.contact_application()
        if isinstance(self.contact, QuerySet):
            await self.fetch_related("contact")
        elif self.contact is None:
            raise EndpointContactRequiredError

        valid = await contact_application.validate_contact_value(
            contact=self.contact, contact_value=self.value
        )
        if raise_exception and not valid:
            raise EndpointInvalidValueError
        return valid

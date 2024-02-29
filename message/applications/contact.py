# Third Party Library
from message import models
from message.applications.base import Application


class ContactApplication(Application[models.Contact]):
    """
    Contact Application
    """

    # required by Application[models.Contact]
    model_class = models.Contact

    async def validate_contact_value(
        self, contact: models.Contact, contact_value: str | dict
    ) -> bool:
        """
        Validate value of contact
        """
        return contact.validate_endpoint_value(contact_value)

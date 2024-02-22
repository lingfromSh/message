# Third Party Library
from message import models
from message.applications.base import Application


class ContactApplication(Application[models.Contact]):
    """
    Contact Application
    """

    # required by Application[models.Contact]
    model_class = models.Contact

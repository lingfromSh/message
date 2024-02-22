# Third Party Library
from message import models
from message.applications.base import Application


class MessageApplication(Application[models.Message]):
    """
    Message Application
    """

    # required by Application
    model_class = models.Message

# Third Party Library
from message import models
from message.applications.base import Application


class UserApplication(Application[models.User]):
    """
    User Application
    """

    model_class = models.User

# Third Party Library
from message import models
from message.applications.base import Application


class ProviderApplication(Application[models.Provider]):
    """
    Provider Application
    """

    # required by Application
    model_class = models.Provider

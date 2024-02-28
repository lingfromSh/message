# Third Party Library
from message import models
from message.applications.base import Application


class ProviderTemplateApplication(Application[models.ProviderTemplate]):
    """
    Provider Template Application
    """

    # required by Application
    model_class = models.ProviderTemplate


class ProviderApplication(Application[models.Provider]):
    """
    Provider Application
    """

    # required by Application
    model_class = models.Provider

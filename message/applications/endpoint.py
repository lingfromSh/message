# Third Party Library
from message import models
from message.applications.base import Application


class EndpointApplication(Application[models.Endpoint]):
    """
    Endpoint Application
    """

    # required by Application
    model_class = models.Endpoint

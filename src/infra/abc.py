# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from pydantic import BaseModel


class HealthStatus(BaseModel):
    is_ready: bool
    state: typing.Literal["recovering", "up", "down"]
    reason: typing.Optional[str] = ""


class Infrastructure(metaclass=ABCMeta):
    async def health_check(self) -> HealthStatus:
        """
        Health check for the infrastructure.
        """
        raise NotImplementedError

    async def init(self):
        """
        Initialize the infrastructure.
        """
        raise NotImplementedError

    async def shutdown(self):
        """
        Shutdown the infrastructure.
        """
        raise NotImplementedError

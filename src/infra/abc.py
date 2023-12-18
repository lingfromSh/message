# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from dependency_injector.resources import AsyncResource
from pydantic import BaseModel


class CheckResult(BaseModel):
    check: str
    status: typing.Literal["up", "down"]
    result: typing.Optional[str] = ""


class HealthStatus(BaseModel):
    status: typing.Literal["up", "down"]
    checks: typing.List[CheckResult]


class Infrastructure(AsyncResource, metaclass=ABCMeta):
    async def health_check(self) -> HealthStatus:
        """
        Health check for the infrastructure.
        """
        raise NotImplementedError

    async def init(self) -> "Infrastructure":
        """
        Initialize the infrastructure.
        """
        raise NotImplementedError

    async def shutdown(self, resource: "Infrastructure"):
        """
        Shutdown the infrastructure.
        """
        raise NotImplementedError

# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from pydantic import BaseModel
from ulid import ULID

# First Library
import exceptions
from infra import get_infra

__registry__ = {}


class ProviderBase(metaclass=ABCMeta):
    # basic info
    name: str
    description: typing.Optional[str]
    supported_contacts: typing.List[str]

    # abilities
    can_recv: bool = False
    can_send: bool = False

    # definitions
    parameter_definition: typing.Optional[BaseModel]
    message_definition: typing.Optional[BaseModel]

    # TODO: subscribers: typing.Any

    def __init__(self, parameters: "parameter_definition"):
        self.infra = get_infra()
        self.parameters = parameters

    def __init_subclass__(cls) -> None:
        global __registry__
        __registry__.update({cls.name: cls})

    async def _send(self, message: typing.Any):
        """
        Send message after check.
        """
        if self.can_send is True:
            return await self.send(message)
        raise exceptions.ProviderSendNotSupportError

    async def _recv(self):
        """
        Receive message after check.
        """
        if self.can_recv is True:
            return await self.recv()
        raise exceptions.ProviderRecvNotSupportError

    @classmethod
    def validate_parameters(
        cls,
        parameters: typing.Dict,
    ) -> "parameter_definition":
        """
        Parameters validation.
        """
        if cls.parameter_definition:
            return cls.parameter_definition.model_validate(parameters)
        return None

    def validate_message(
        self,
        message: typing.Any,
    ) -> "message_definition":
        """
        Message validation.
        """
        if self.message_definition:
            return self.message_definition.model_validate(message)
        return None

    async def send(self, message):
        """
        Custom logic: send message.
        """
        raise NotImplementedError

    async def recv(self):
        """
        Custom logic: recv message.
        """
        raise NotImplementedError

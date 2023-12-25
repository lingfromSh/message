# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from pydantic import BaseModel

# First Library
import exceptions

__registry__ = {}


class ProviderBase(metaclass=ABCMeta):
    # basic info
    name: str
    description: typing.Optional[str]
    supported_contacts: typing.List[str]

    # abilities
    can_recv: bool
    can_send: bool

    # definitions
    parameter_definition: typing.Optional[BaseModel]
    message_definition: typing.Optional[BaseModel]

    # TODO: subscribers: typing.Any

    def __init__(self, infra, parameters: "parameter_definition"):
        self.infra = infra
        self.parameters = parameters

    def __init_subclass__(cls) -> None:
        global __registry__
        __registry__.update({cls.name: cls})

    async def _send(
        self,
        message: "message_definition",
        *,
        users: typing.List[typing.Any] = None,
        endpoints: typing.List[typing.Any] = None,
        background: bool = True,
    ):
        """
        Send message after check.
        """
        if self.can_send is True:
            await self.send(
                message,
                users=users,
                endpoints=endpoints,
                background=background,
            )
        raise exceptions.ProviderSendNotSupportError

    async def _recv(self):
        """
        Receive message after check.
        """
        if self.can_recv is True:
            await self.recv()
        raise exceptions.ProviderRecvNotSupportError

    def validate_parameters(
        self,
        parameters: typing.Dict,
    ) -> "parameter_definition":
        """
        Parameters validation.
        """
        if self.parameter_definition:
            return self.parameter_definition.model_validate(parameters)
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

    async def send(
        self,
        message: "message_definition",
        *,
        users: typing.List[typing.Any] = None,
        endpoints: typing.List[typing.Any] = None,
        background: bool = True,
    ):
        """
        Custom logic: send message.
        """
        raise NotImplementedError

    async def recv(self):
        """
        Custom logic: recv message.
        """
        raise NotImplementedError

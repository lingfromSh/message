# Standard Library
import typing
from abc import ABCMeta

# Third Party Library
from message import exceptions
from message.infra import get_infra
from pydantic import BaseModel

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
        if self.parameter_definition:
            self.parameters = self.parameter_definition.model_validate(parameters)
        else:
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
            if isinstance(message, str):
                return self.message_definition.model_validate_json(message)
            else:
                return self.message_definition.model_validate(message)
        return None

    def validate_contacts(self, contacts: typing.List[typing.Any]):
        """
        Validate contacts.
        """
        if not contacts:
            return []
        if not self.supported_contacts:
            return []
        validated_contacts = []
        for contact in contacts:
            for contact_schema in self.supported_contacts:
                try:
                    contact_schema.__pydantic_model__.model_validate(contact)
                    validated_contacts.append(contact)
                except Exception:
                    continue
        return validated_contacts

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

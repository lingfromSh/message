from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from apps.message.common.constants import MessageProviderType
from common.exceptions import ImproperlyConfiguredException

__all__ = ["MessageProviderModel"]


@dataclass
class MessageProviderInfoOption:
    """
    A class to represent provider's info
    """

    name: str
    description: Optional[str]
    type: MessageProviderType

    @classmethod
    def from_cls(cls, klass) -> MessageProviderInfoOption:
        name = getattr(klass, "name", None)
        type = getattr(klass, "type", None)
        desc = getattr(klass, "description", None)

        if name is None:
            raise ImproperlyConfiguredException("a message provider must have a name")

        if type is None:
            raise ImproperlyConfiguredException("a message provider must have a type")

        return cls(name=name, description=desc, type=type)


@dataclass
class MessageProviderCapabilityOption:
    """
    A class to represent provider's capabilities
    """

    is_enabled: bool
    can_send: bool

    @classmethod
    def from_cls(cls, pdict, klass) -> MessageProviderCapabilityOption:
        is_enabled = getattr(klass, "is_enabled", True)
        can_send = getattr(klass, "can_send", True)

        if not can_send:
            return cls(is_enabled=is_enabled, can_send=can_send)

        if not pdict.get("send"):
            raise ImproperlyConfiguredException(
                "provider must implment send method when can_send=True"
            )

        if not callable(pdict["send"]):
            raise ImproperlyConfiguredException("send must be callable")

        return cls(is_enabled=is_enabled, can_send=can_send)


class MessageProviderConfigOption:
    """
    A class to represent provider's config.
    if your provider does not need additional config, this part is optional.
    """

    def __init__(self, config_model) -> None:
        self.config_model = config_model

    @classmethod
    def from_cls(cls, klass) -> MessageProviderConfigOption:
        print(issubclass(klass, BaseModel))
        if not issubclass(klass, BaseModel):
            raise ImproperlyConfiguredException(
                "a config model must be subclass of pydantic's BaseModel"
            )
        return cls(config_model=klass)

    def validate(self, raw_config) -> BaseModel:
        return self.config_model.model_validate(raw_config)


class MessageProviderMessageOption:
    """
    A class to represent provider's message format.
    """

    def __init__(self, message_model):
        self.message_model = message_model

    @classmethod
    def from_cls(cls, klass) -> MessageProviderMessageOption:
        if not issubclass(klass, BaseModel):
            raise ImproperlyConfiguredException(
                "a message model must be subclass of pydantic's BaseModel"
            )
        return cls(message_model=klass)

    def validate(self, raw_message) -> BaseModel:
        return self.message_model.model_validate(raw_message)


class MessageProviderModelMetaClass(type):
    """
    A metaclass to ensure a provider class have required params
    """

    @classmethod
    def get_from_ancestors(cls, clsbases, name):
        for clsbase in clsbases:
            if not hasattr(clsbase, name):
                continue
            return getattr(clsbase, name)

    def __new__(mcs, clsname, clsbases, clsdict):
        print(clsname, clsbases, clsdict)
        if clsdict.get("ABSTRACT"):
            return super().__new__(mcs, clsname, clsbases, clsdict)

        # init Info option
        InfoModel = clsdict.get("Info") or mcs.get_from_ancestors(clsbases, "Info")
        if not InfoModel:
            raise ImproperlyConfiguredException(
                "a message provider must have an Info model"
            )
        info_option = MessageProviderInfoOption.from_cls(InfoModel)
        clsdict["info"] = info_option

        # init Capability option
        CapabilityModel = clsdict.get("Capability") or mcs.get_from_ancestors(
            clsbases, "Capability"
        )
        if not CapabilityModel:
            raise ImproperlyConfiguredException(
                "a message provider must have a capability model"
            )
        capability_option = MessageProviderCapabilityOption.from_cls(
            clsdict, CapabilityModel
        )
        clsdict["capability"] = capability_option

        # init Message option
        MessageModel = clsdict.get("Message") or mcs.get_from_ancestors(
            clsbases, "Message"
        )
        if not MessageModel:
            raise ImproperlyConfiguredException(
                "a message provider must have a message model"
            )
        clsdict["message_model"] = MessageProviderMessageOption.from_cls(MessageModel)

        # init Config option
        if "Config" in clsdict or mcs.get_from_ancestors(clsbases, "Config"):
            ConfigModel = clsdict.get("Config") or mcs.get_from_ancestors(
                clsbases, "Config"
            )
            clsdict["config_model"] = MessageProviderConfigOption.from_cls(ConfigModel)

        return super().__new__(mcs, clsname, clsbases, clsdict)


class MessageProviderModel(metaclass=MessageProviderModelMetaClass):
    """
    A model to represent a message provider
    """

    ABSTRACT = True

    def __init_subclass__(cls) -> None:
        setattr(cls, "ABSTRACT", False)

    def __init__(self, **kwargs):
        if hasattr(self, "config_model"):
            validated = self.config_model.validate(kwargs)
            self.config = validated
        else:
            self.config = None

    def schema(self) -> dict:
        schema = {
            "info": self.info,
            "capability": self.capability,
        }

        if hasattr(self, "config_model"):
            schema["config_model"] = self.config_model.dict()

        if hasattr(self, "message_model"):
            schema["message_model"] = self.message_model.dict()

        return schema

    async def send(self, message):
        raise NotImplementedError

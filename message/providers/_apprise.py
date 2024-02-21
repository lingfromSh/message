# Standard Library
import re
import typing

# Third Party Library
import stringcase
from apprise import Apprise
from apprise.NotificationManager import NotificationManager
from pydantic import BaseModel
from pydantic import Field
from pydantic import create_model
from pydantic import field_serializer
from pydantic import field_validator

# Local Folder
from .abc import ProviderBase

converter = {}


def convert(plugin):
    # NOTE: apprise can handle dict url params, so we don't need care about map_to.
    protocol = plugin.protocol
    secure_protocol = plugin.secure_protocol
    service_name = str(plugin.service_name)
    service_url = plugin.service_url
    setup_url = plugin.setup_url

    protocols = []
    if isinstance(protocol, str):
        protocols.append(protocol)
    elif isinstance(protocol, (list, tuple)):
        protocols.extend(protocol)
    if isinstance(secure_protocol, str):
        protocols.append(secure_protocol)
    elif isinstance(secure_protocol, (list, tuple)):
        protocols.extend(secure_protocol)

    # 必填参数
    tokens = getattr(plugin, "template_tokens", None)
    # 可选参数
    args = getattr(plugin, "template_args", None)
    # 特殊参数，用在header中
    kwargs = getattr(plugin, "template_kwargs", None)

    connection_parameters = {
        "protocol": (typing.Literal[*protocols], ...)  # type:ignore
    }
    message_parameters = {}
    if isinstance(tokens, dict):
        for token_name, token_config in tokens.items():
            token_type = token_config.get("type", "")

            if "target" in token_name:
                continue

            if token_type.endswith("string"):
                constraints = {}
                if regex := token_config.get("regex"):
                    if isinstance(regex, (list, tuple)):
                        regex = regex[0]
                    try:
                        re.compile(regex, re.IGNORECASE)
                    except Exception:
                        continue
                    constraints["pattern"] = regex
                if constraints:
                    raw_type = typing.Annotated[str, Field(**constraints)]
                else:
                    raw_type = str
            elif token_type.endswith("int"):
                constraints = {}
                if min_value := token_config.get("min"):
                    constraints["gt"] = min_value - 1
                if max_value := token_config.get("max"):
                    constraints["lt"] = max_value + 1
                if constraints:
                    raw_type = typing.Annotated[int, Field(**constraints)]
                else:
                    raw_type = int
            elif token_type.endswith("bool"):
                raw_type = bool
            elif token_type.endswith("float"):
                raw_type = float

            if token_type.startswith("list:"):
                raw_type = typing.List[raw_type]

            if token_type.startswith("choice:") and token_config.get("values"):
                choices = token_config["values"]
                raw_type = typing.Literal[*choices]  # type: ignore

            if token_config.get("required", True) is False:
                raw_type = typing.Optional[raw_type]

            if default := token_config.get("default"):
                annotation = (raw_type, default)
            else:
                annotation = (raw_type, ...)

            connection_parameters[token_name] = annotation

    if isinstance(plugin.title_maxlen, int) and plugin.title_maxlen != 0:
        message_parameters["title"] = (
            typing.Annotated[str, Field(max_length=plugin.title_maxlen)],
            None,
        )
    if isinstance(plugin.body_maxlen, int) and plugin.body_maxlen != 0:
        message_parameters["body"] = (
            typing.Annotated[str, Field(max_length=plugin.body_maxlen)],
            None,
        )
    if plugin.attachment_support is True:
        message_parameters["attachments"] = (str, None)

    if service_name.isalnum():
        code = stringcase.pascalcase(service_name.lower()).lower()
    else:
        code = stringcase.lowercase(protocols[0])

    newcls = type(
        f"Apprise{stringcase.pascalcase(code)}Provider",
        (ProviderBase,),
        {
            "name": code,
            "description": "Apprise Provider - {name}\nService: {service_url}\nSetup: {setup_url}".format(
                name=service_name, service_url=service_url, setup_url=setup_url
            ),
            "can_send": True,
            "supported_contacts": [],  # TODO: 将apprise的target值转换为ContactEnum
            "parameter_definition": create_model(
                f"Apprise{stringcase.pascalcase(code)}ProviderParameterDefinition",
                **connection_parameters,
            ),
            "message_definition": create_model(
                f"Apprise{stringcase.pascalcase(code)}ProviderMessageDefinition",
                **message_parameters,
            ),
        },
    )


def apprise_provider_converter(service_name: str):
    def wrapper(func):
        def wrapper_func(*args, **kwargs):
            return func(*args, **kwargs)

    return wrapper


def get_apprise_provider_converter(service_name: str):
    return converter.get(service_name, convert)


apprise_providers = []
manager = NotificationManager()
for plugin in manager.plugins(include_disabled=False):
    converter = get_apprise_provider_converter(service_name=plugin.service_name)
    provider = converter(plugin)
    apprise_providers.append(provider)

# 如何解决target的转换成pydantic可以校验的类型
# 如何解决apprise里不同provider但是共享target的情况

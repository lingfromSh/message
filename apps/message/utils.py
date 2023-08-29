from typing import List
from apps.message.common.constants import MessageProviderType
from apps.message.providers.base import MessageProviderModel


def get_provider(type: MessageProviderType, code: str) -> MessageProviderModel:
    from apps.message.providers.base import __registries__

    try:
        return __registries__[type, code]
    except KeyError:
        raise ValueError(f"provider({type.value}, {code}) does not exist")


def get_provider_message_template_fields(
    type: MessageProviderType, code: str
) -> List[str]:
    provider = get_provider(type, code)
    template_fields = [
        field.name for field in provider.message_model.fields if field.for_template
    ]
    return template_fields

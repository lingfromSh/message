from apps.message.common.constants import MessageProviderType
from apps.message.providers.base import MessageProviderModel


def get_provider(type: MessageProviderType, code: str) -> MessageProviderModel:
    from apps.message.providers.base import __registries__

    try:
        return __registries__[type, code]
    except KeyError:
        raise ValueError(f"provider({type.value}, {code}) does not exist")

# Standard Library
import asyncio

# Third Party Library
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

# First Library
from common.constants import SETTINGS_YAML
from infra.persistence import PersistenceInfrastructure
from infra.storage import StorageInfrastructure

__infra__ = None


class InfrastructureContainer(DeclarativeContainer):
    config = providers.Configuration()

    persistence = providers.Resource(
        PersistenceInfrastructure,
        dsn=config.persistence.dsn,
    )

    storage = providers.Resource(
        StorageInfrastructure,
        mode=config.storage.mode,
        options=config.storage.options,
    )


async def initialize_infra() -> InfrastructureContainer:
    global __infra__
    __infra__ = InfrastructureContainer()
    __infra__.config.from_yaml(SETTINGS_YAML)
    await __infra__.init_resources()
    return __infra__


async def shutdown_infra() -> None:
    global __infra__
    await asyncio.shield(__infra__.shutdown_resources())
    __infra__ = None


def get_infra() -> InfrastructureContainer:
    return __infra__

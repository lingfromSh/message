# Third Party Library
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

# First Library
from common.constants import SETTINGS_YAML
from infra.storage import StorageInfrastructure


class InfrastructureContainer(DeclarativeContainer):
    config = providers.Configuration()

    storage = providers.Singleton(
        StorageInfrastructure,
        mode=config.storage.mode,
        options=config.storage.options,
    )


def get_infra() -> InfrastructureContainer:
    infra = InfrastructureContainer()
    infra.config.from_yaml(SETTINGS_YAML)
    return infra


infra = get_infra()

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


async def initialize_infra(app) -> InfrastructureContainer:
    global __infra__
    __infra__ = InfrastructureContainer()
    __infra__.config.from_yaml(SETTINGS_YAML)
    await __infra__.init_resources()
    return __infra__


async def shutdown_infra(app) -> None:
    global __infra__
    await asyncio.shield(__infra__.shutdown_resources())
    __infra__ = None


def get_infra() -> InfrastructureContainer:
    return __infra__


async def infra_check(*infra_names: list[str], raise_exceptions: bool = True) -> bool:
    infra = get_infra()
    for infra_name in infra_names:
        if not getattr(infra, infra_name):
            raise RuntimeError(f"Infra {infra_name} not initialized")
        _infra = await getattr(infra, infra_name)()
        status = await _infra.health_check()
        if status.status != "up":
            if raise_exceptions:
                raise RuntimeError(
                    f"Infra {infra_name} {status.status}\n{status.checks}"
                )
            return False


def sync_infra_check(*infra_names: list[str], raise_exceptions: bool = True) -> bool:
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(
            infra_check(*infra_names, raise_exceptions=raise_exceptions)
        )
    except RuntimeError:
        return asyncio.run(infra_check(*infra_names, raise_exceptions=raise_exceptions))

# Standard Library
import asyncio
import typing

# Third Party Library
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

# First Library
from common.constants import SETTINGS_YAML
from infra.background import BackgroundSchedulerInfrastructure
from infra.cache import CacheInfrastructure
from infra.persistence import PersistenceInfrastructure
from infra.queue import QueueInfrastructure
from infra.storage import StorageInfrastructure
from infra.websocket import WebsocketInfrastructure

__infra__ = None


class InfrastructureContainer(DeclarativeContainer):
    config = providers.Configuration()

    background_scheduler: typing.Callable[
        [], typing.Awaitable[BackgroundSchedulerInfrastructure]
    ] = providers.Resource(BackgroundSchedulerInfrastructure)

    cache: typing.Callable[
        [], typing.Awaitable[CacheInfrastructure]
    ] = providers.Resource(
        CacheInfrastructure,
        url=config.cache.dsn,
    )

    queue: typing.Callable[
        [], typing.Awaitable[QueueInfrastructure]
    ] = providers.Resource(
        QueueInfrastructure,
        url=config.queue.dsn,
    )

    persistence: typing.Callable[
        [], typing.Awaitable[PersistenceInfrastructure]
    ] = providers.Resource(
        PersistenceInfrastructure,
        dsn=config.persistence.dsn,
    )

    storage: typing.Callable[
        [], typing.Awaitable[StorageInfrastructure]
    ] = providers.Resource(
        StorageInfrastructure,
        mode=config.storage.mode,
        options=config.storage.options,
    )

    websocket: typing.Callable[
        [], typing.Awaitable[WebsocketInfrastructure]
    ] = providers.Resource(
        WebsocketInfrastructure,
        background_scheduler=background_scheduler,
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
            raise SystemError(f"Infra {infra_name} not initialized")
        _infra = await getattr(infra, infra_name)()
        status = await _infra.health_check()
        if status.status != "up":
            if raise_exceptions:
                raise SystemError(f"Infra {infra_name} {status.status}")
            return False
    return True

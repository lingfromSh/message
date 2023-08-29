from dependency_injector import containers, providers
from .queue import QueueDependency
from .cache import CacheDependency


class Infrastructure(containers.DeclarativeContainer):
    config = providers.Configuration()

    queue = providers.Singleton(
        QueueDependency,
        host=config.QUEUE.HOST,
        port=config.QUEUE.PORT,
        username=config.QUEUE.USERNAME,
        password=config.QUEUE.PASSWORD,
    )

    cache = providers.Singleton(
        CacheDependency,
        sentinel_host=config.CACHE.SENTINEL_HOST,
        sentinel_port=config.CACHE.SENTINEL_PORT,
        sentinel_password=config.CACHE.SENTINEL_PASSWORD,
        master_set=config.CACHE.MASTER_SET,
        master_password=config.CACHE.MASTER_PASSWORD,
    )

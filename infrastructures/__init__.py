from dependency_injector import containers
from dependency_injector import providers
from sanic import Sanic

from .cache import CacheDependency
from .mongodb import MongoDBDependency
from .queue import QueueDependency
from .websocket import WebsocketPoolDependency


class Infrastructure(containers.DeclarativeContainer):
    app = providers.Dependency(instance_of=Sanic)
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

    database = providers.Singleton(
        MongoDBDependency,
        user=config.DATABASE.USER,
        password=config.DATABASE.PASSWORD,
        host=config.DATABASE.HOST,
        port=config.DATABASE.PORT,
    )

    websocket = providers.Singleton(WebsocketPoolDependency, app=app)

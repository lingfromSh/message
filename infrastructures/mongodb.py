from motor.motor_asyncio import AsyncIOMotorClient
from sanic.log import logger
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance


class MongoDBDependency:
    def __init__(
        self,
        host,
        port,
        user,
        password,
        max_pool_size: int = 1000,
        max_connecting: int = 1000,
    ):
        self.uri = "mongodb://{user}:{passwd}@{host}:{port}/?replicaSet=message-replicas".format(
            user=user,
            passwd=password,
            host=host,
            port=port,
        )
        self.client = AsyncIOMotorClient(
            self.uri, maxPoolSize=max_pool_size, maxConnecting=max_connecting
        )
        self.db = self.client.message
        self.doc_instance = MotorAsyncIOInstance(self.db)
        logger.info("dependency: mongodb is configured")

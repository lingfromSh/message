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
        rs="message-replicas",
        max_pool_size: int = 10,
        max_connecting: int = 1000,
    ):
        self.uri = "mongodb://{user}:{passwd}@{host}:{port}/?replicaSet={rs}".format(
            user=user,
            passwd=password,
            host=host,
            port=port,
            rs=rs,
        )
        self.client = AsyncIOMotorClient(
            self.uri, maxPoolSize=max_pool_size, maxConnecting=max_connecting
        )
        self.db = self.client.message
        self.doc_instance = MotorAsyncIOInstance(self.db)
        logger.debug("dependency: mongodb is configured")

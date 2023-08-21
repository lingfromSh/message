from motor.motor_asyncio import AsyncIOMotorClient
from sanic.log import logger
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

from common.depend import Dependency


class MongoDBDependency(Dependency, dependency_name="MongoDB", dependency_alias="mdb"):
    @property
    def uri(self):
        return "mongodb://{user}:{passwd}@{host}:{port}/?replicaSet=message-replicas".format(
            user=self.app.config.DATABASE.USER,
            passwd=self.app.config.DATABASE.PASSWORD,
            host=self.app.config.DATABASE.HOST,
            port=self.app.config.DATABASE.PORT,
        )

    async def prepare(self) -> bool:
        self._db_client = AsyncIOMotorClient(
            self.uri, maxPoolSize=200, maxConnecting=200
        )
        self._prepared = self._db_client.message
        self.app.ctx.doc_instance = MotorAsyncIOInstance(self._prepared)
        self.app.ctx.db_client = self._db_client
        self.is_prepared = True
        # logger.info("dependency:MongoDB is prepared")
        return self.is_prepared

    async def check(self) -> bool:
        return True

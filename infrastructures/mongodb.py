from motor.motor_asyncio import AsyncIOMotorClient
from sanic.log import logger
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

from common.depend import Dependency


class MongoDBDependency(Dependency, dependency_name="MongoDB", dependency_alias="mdb"):
    @property
    def uri(self):
        return "mongodb://{user}:{passwd}@{host}:{port}".format(
            user=self.app.config.DATABASE.USER,
            passwd=self.app.config.DATABASE.PASSWORD,
            host=self.app.config.DATABASE.HOST,
            port=self.app.config.DATABASE.PORT,
        )

    async def prepare(self) -> bool:
        self._prepared = AsyncIOMotorClient(self.uri).message
        self.app.ctx.doc_instance = MotorAsyncIOInstance(self._prepared)
        self.is_prepared = True
        logger.info("dependency:MongoDB is prepared")
        return self.is_prepared

    async def check(self) -> bool:
        return True

from common.depend import Dependency


class MongoDBDependency(Dependency, dependency_name="MongoDB", dependency_alias="mdb"):
    async def prepare(self) -> bool:
        self.is_prepared = True
        return self.is_prepared

    async def check(self) -> bool:
        return True

from common.depend import Dependency


class QueueDependency(Dependency, dependency_name="Queue", dependency_alias="queue"):
    async def prepare(self) -> bool:
        self.is_prepared = True
        return self.is_prepared

    async def check(self) -> bool:
        return True

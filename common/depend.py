import abc
from typing import Any

from common.health import HealthChecker


class Dependency(HealthChecker, metaclass=abc.ABCMeta):
    def __init__(self, app):
        self.app = app
        self.is_prepared = False
        self._prepared = None
        self._register()

    def __init_subclass__(cls, dependency_name: str, dependency_alias: str) -> None:
        setattr(cls, "name", dependency_name)
        setattr(cls, "alias", dependency_alias)

    def __getattribute__(self, name: str) -> Any:
        try:
            return object.__getattribute__(
                object.__getattribute__(self, "_prepared"), name
            )
        except AttributeError:
            return object.__getattribute__(self, name)

    def _register(self):
        setattr(self.app.ctx, self.alias, self)

    @abc.abstractmethod
    async def prepare(self) -> bool:
        raise NotImplementedError

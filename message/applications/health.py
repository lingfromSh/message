# Third Party Library
from message.infra import get_infra
from message.infra.abc import HealthStatus
from pydantic import BaseModel


class ServiceHealthStatus(BaseModel):
    cache: HealthStatus
    persistence: HealthStatus
    storage: HealthStatus
    websocket: HealthStatus
    background: HealthStatus


class HealthApplication:
    def __init__(self) -> None:
        self.infra = get_infra()

    async def get_service_health(self) -> ServiceHealthStatus:
        return ServiceHealthStatus(
            cache=await self.get_cache_health(),
            persistence=await self.get_persistence_health(),
            storage=await self.get_storage_health(),
            websocket=await self.get_websocket_health(),
            background=await self.get_background_health(),
        )

    async def get_cache_health(self) -> HealthStatus:
        cache = await self.infra.cache()
        return await cache.health_check()

    async def get_persistence_health(self) -> HealthStatus:
        persistence = await self.infra.persistence()
        return await persistence.health_check()

    async def get_storage_health(self) -> HealthStatus:
        storage = await self.infra.storage()
        return await storage.health_check()

    async def get_websocket_health(self) -> HealthStatus:
        websocket = await self.infra.websocket()
        return await websocket.health_check()

    async def get_background_health(self) -> HealthStatus:
        background = await self.infra.background_scheduler()
        return await background.health_check()

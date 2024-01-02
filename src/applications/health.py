# Third Party Library
from pydantic import BaseModel

# First Library
from infra import get_infra
from infra.abc import HealthStatus


class ServiceHealthStatus(BaseModel):
    cache: HealthStatus
    persistence: HealthStatus
    storage: HealthStatus
    websocket: HealthStatus
    background: HealthStatus


class HealthApplication:
    async def get_service_health(self) -> ServiceHealthStatus:
        return ServiceHealthStatus(
            cache=await self.get_cache_health(),
            persistence=await self.get_persistence_health(),
            storage=await self.get_storage_health(),
            websocket=await self.get_websocket_health(),
            background=await self.get_background_health(),
        )

    async def get_cache_health(self) -> HealthStatus:
        infra = get_infra()

        cache = await infra.cache()
        return await cache.health_check()

    async def get_persistence_health(self) -> HealthStatus:
        infra = get_infra()

        persistence = await infra.persistence()
        return await persistence.health_check()

    async def get_storage_health(self) -> HealthStatus:
        infra = get_infra()

        storage = await infra.storage()
        return await storage.health_check()

    async def get_websocket_health(self) -> HealthStatus:
        infra = get_infra()

        websocket = await infra.websocket()
        return await websocket.health_check()

    async def get_background_health(self) -> HealthStatus:
        infra = get_infra()

        background = await infra.background_scheduler()
        return await background.health_check()

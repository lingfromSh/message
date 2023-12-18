# Third Party Library
from pydantic import BaseModel

# First Library
from infra import get_infra
from infra.abc import HealthStatus


class ServiceHealthStatus(BaseModel):
    persistence: HealthStatus
    storage: HealthStatus


class HealthApplication:
    async def get_service_health(self) -> ServiceHealthStatus:
        return ServiceHealthStatus(
            persistence=await self.get_persistence_health(),
            storage=await self.get_storage_health(),
        )

    async def get_persistence_health(self) -> HealthStatus:
        infra = get_infra()

        persistence = await infra.persistence()
        return await persistence.health_check()

    async def get_storage_health(self) -> HealthStatus:
        infra = get_infra()

        storage = await infra.storage()
        return await storage.health_check()

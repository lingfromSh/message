# Third Party Library
import anyio
import strawberry
from pydantic import TypeAdapter
from pydantic import conint

# First Library
from apis.health.objectypes import StrawberryHealthStatus
from apis.health.objectypes import StrawberryServiceHealthStatus
from applications.health import HealthApplication


@strawberry.type(description="Health API")
class Query:
    @strawberry.field
    async def health_status_all(
        self,
    ) -> StrawberryServiceHealthStatus:
        application = HealthApplication()
        return await application.get_service_health()

    @strawberry.field
    async def health_status_persistence(self) -> StrawberryHealthStatus:
        application = HealthApplication()
        return await application.get_persistence_health()

    @strawberry.field
    async def health_status_stroage(self) -> StrawberryHealthStatus:
        application = HealthApplication()
        return await application.get_storage_health()


@strawberry.type(description="Health API")
class Subscription:
    @strawberry.subscription
    async def health_status_all(
        self, refresh_interval: int = 5
    ) -> StrawberryServiceHealthStatus:
        application = HealthApplication()
        refresh_interval = TypeAdapter(conint(gt=0, lt=900)).validate_python(
            refresh_interval
        )
        while True:
            yield await application.get_service_health()
            await anyio.sleep(refresh_interval)

    @strawberry.subscription
    async def health_status_persistence(
        self, refresh_interval: int = 5
    ) -> StrawberryHealthStatus:
        application = HealthApplication()
        refresh_interval = TypeAdapter(conint(gt=0, lt=900)).validate_python(
            refresh_interval
        )
        while True:
            yield await application.get_persistence_health()
            await anyio.sleep(refresh_interval)

    @strawberry.subscription
    async def health_status_storage(
        self, refresh_interval: int = 5
    ) -> StrawberryHealthStatus:
        application = HealthApplication()
        refresh_interval = TypeAdapter(conint(gt=0, lt=900)).validate_python(
            refresh_interval
        )
        while True:
            yield await application.get_storage_health()
            await anyio.sleep(refresh_interval)

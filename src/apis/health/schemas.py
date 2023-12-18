# Third Party Library
import anyio
import strawberry
from pydantic import TypeAdapter
from pydantic import conint

# First Library
from apis.health.objectypes import StrawberryServiceHealthStatus
from applications.health import HealthApplication


@strawberry.type
class Query:
    @strawberry.field
    async def service_health_status(
        self,
    ) -> StrawberryServiceHealthStatus:
        application = HealthApplication()
        return await application.get_service_health()


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def service_health_status(
        self, refresh_interval: int = 5
    ) -> StrawberryServiceHealthStatus:
        application = HealthApplication()
        refresh_interval = TypeAdapter(conint(gt=0, lt=900)).validate_python(
            refresh_interval
        )
        while True:
            yield await application.get_service_health()
            await anyio.sleep(refresh_interval)

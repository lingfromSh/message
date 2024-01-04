# Third Party Library
import anyio
import strawberry
from message.apis.health.objectypes import StrawberryServiceHealthStatus
from message.applications.health import HealthApplication
from pydantic import TypeAdapter
from pydantic import conint


@strawberry.type(description="Health API")
class Query:
    @strawberry.field
    async def health_status_all(
        self,
    ) -> StrawberryServiceHealthStatus:
        application = HealthApplication()
        return await application.get_service_health()


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

# Standard Library
import typing

# Third Party Library
import anyio
import strawberry
from message.apis.health.objectypes import StrawberryServiceHealthStatus
from message.wiring import ApplicationContainer
from pydantic import TypeAdapter
from pydantic import conint


@strawberry.type(description="Health API")
class Query:
    @strawberry.field
    async def health_status_all(
        self,
    ) -> StrawberryServiceHealthStatus:
        application = ApplicationContainer.health_application()
        return await application.get_service_health()


@strawberry.type(description="Health API")
class Subscription:
    @strawberry.subscription
    async def health_status_all(
        self, refresh_interval: int = 5
    ) -> typing.AsyncGenerator[StrawberryServiceHealthStatus, None]:
        application = ApplicationContainer.health_application()
        refresh_interval = TypeAdapter(conint(gt=0, lt=900)).validate_python(
            refresh_interval
        )
        while True:
            yield await application.get_service_health()
            await anyio.sleep(refresh_interval)

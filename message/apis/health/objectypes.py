# Standard Library
import typing

# Third Party Library
import strawberry
from message.infra.abc import CheckResult
from message.infra.abc import HealthStatus

# TODO: we need to find a easier way to convert pydantic model to strawberry type, so we could reduce this boring work.


@strawberry.experimental.pydantic.type(model=CheckResult)
class StrawberryCheckResult:
    check: str
    status: str
    result: typing.Optional[str] = ""


@strawberry.experimental.pydantic.type(model=HealthStatus)
class StrawberryHealthStatus:
    status: str
    checks: typing.List[StrawberryCheckResult]


@strawberry.type
class StrawberryServiceHealthStatus:
    cache: StrawberryHealthStatus
    persistence: StrawberryHealthStatus
    storage: StrawberryHealthStatus
    websocket: StrawberryHealthStatus
    background: StrawberryHealthStatus

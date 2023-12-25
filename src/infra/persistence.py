# Third Party Library
from tortoise import Tortoise

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus
from infra.abc import Infrastructure


class PersistenceInfrastructure(Infrastructure):
    async def health_check(self) -> HealthStatus:
        if not Tortoise._inited:
            return HealthStatus(
                status="down",
                checks=[
                    CheckResult(
                        check="init check",
                        status="down",
                        result="failed to init",
                    )
                ],
            )
        try:
            await Tortoise.get_connection("default").execute_query("")
            return HealthStatus(
                status="up",
                checks=[
                    CheckResult(
                        check="init check",
                        status="up",
                        result="inited",
                    )
                ],
            )
        except BaseException as e:
            return HealthStatus(
                status="down",
                checks=[
                    CheckResult(
                        check="init check",
                        status="down",
                        result="failed to connect",
                    )
                ],
            )

    async def init(self, dsn: str):
        try:
            await Tortoise.init(
                config={
                    "connections": {"default": dsn},
                    "apps": {
                        "models": {
                            "models": ["models"],
                            "default_connection": "default",
                        }
                    },
                },
                use_tz=True,
            )
            await Tortoise.generate_schemas()
        except BaseException:
            return self
        return self

    async def shutdown(self, resource: "PersistenceInfrastructure"):
        try:
            await Tortoise.close_connections()
        except BaseException:
            pass

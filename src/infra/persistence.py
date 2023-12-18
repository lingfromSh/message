# Third Party Library
from tortoise import Tortoise

# First Library
from infra.abc import Infrastructure


class PersistenceInfrastructure(Infrastructure):
    async def init(self, dsn: str):
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

    async def shutdown(self, _: None):
        await Tortoise.close_connections()

# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
from fastapi import FastAPI
from message.apis import schema
from message.helpers.decorators import ensure_infra
from message.helpers.toml import read_toml
from message.infra import initialize_infra
from message.infra import shutdown_infra
from message.wiring import ApplicationContainer
from strawberry.fastapi.router import GraphQLRouter
from tortoise.transactions import in_transaction


async def initialize_graphql_api(app: FastAPI):
    """
    initialize graphql api
    """

    graphql_router = GraphQLRouter(schema)
    app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])


@ensure_infra("persistence")
async def initialize_fixtures(app: FastAPI):
    """
    initialize fixtures

    1. load builtin contacts from toml file, and create or update them in database.
    """
    # Third Party Library

    try:
        # use absolute path of toml file
        builtin_contacts = await read_toml(
            "/app/message/fixtures/builtin_contacts.toml"
        )
    except (FileNotFoundError, ValueError):
        builtin_contacts = {"contacts": []}

    application = ApplicationContainer.contact_application()
    async with in_transaction():
        existed_builtin_contacts = {}
        async for contact in await application.get_many(filters={"is_builtin": True}):
            existed_builtin_contacts[contact.code] = contact

        for builtin_contact in builtin_contacts["contacts"]:
            if builtin_contact["code"] not in existed_builtin_contacts:
                await application.create(
                    **builtin_contact,
                    is_builtin=True,
                )
            else:
                contact = existed_builtin_contacts[builtin_contact["code"]]
                await application.update(
                    contact,
                    **builtin_contact,
                    is_builtin=True,
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager that ensures that the application is started and stopped
    before and after the context manager.
    """
    application_container = ApplicationContainer()
    application_container.wire(modules=[__name__])

    # initialize infrastructure container
    await initialize_infra(app)
    # initialize fixtures
    await initialize_fixtures(app)
    # initialize graphql api
    await initialize_graphql_api(app)

    yield

    # shutdown infrastructure container
    await shutdown_infra(app)

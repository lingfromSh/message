# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
from fastapi import FastAPI
from message.apis import schema
from message.common.constants import QUEUE_NAME
from message.helpers.decorators import ensure_infra
from message.infra import get_infra
from message.infra import initialize_infra
from message.infra import shutdown_infra
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
    """
    # Third Party Library
    import message.contacts
    from message.applications import ContactApplication
    from message.models.contact import Contact

    application = ContactApplication()
    async with in_transaction():
        for code in Contact.get_schemas().keys():
            try:
                contact = await application.get_contact_by_code(code=code)
                await contact.set_name(name=code.capitalize(), save=False)
                await contact.set_description(description=code, save=False)
                await contact.set_definition(
                    definition={"type": "pydantic", "contact_schema": code},
                    save=False,
                )
                await contact.save()
            except Exception:
                await application.create_contact(
                    name=code.capitalize(),
                    code=code,
                    description=code,
                    definition={"type": "pydantic", "contact_schema": code},
                )


async def initialize_signals(app: FastAPI):
    """
    import signal handlers
    """
    # Third Party Library
    import message.helpers.signals


async def shutdown_eventbus(app: FastAPI, eventbus):
    await eventbus.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager that ensures that the application is started and stopped
    before and after the context manager.
    """
    # initialize infrastructure container
    await initialize_infra(app)
    # initialize graphql api
    await initialize_graphql_api(app)
    # initialize fixtures
    await initialize_fixtures(app)
    # initialize signals
    await initialize_signals(app)

    yield

    # shutdown infrastructure container
    await shutdown_infra(app)

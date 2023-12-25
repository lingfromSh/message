# Standard Library
import gc
from contextlib import asynccontextmanager

# Third Party Library
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from strawberry.fastapi.router import GraphQLRouter
from tortoise.transactions import in_transaction

# First Library
from apis import schema
from helpers.decorators import ensure_infra
from infra import initialize_infra
from infra import shutdown_infra


async def initialize_graphql_api(app: FastAPI):
    """
    initialize graphql api
    """
    graphql_router = GraphQLRouter(schema)
    app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])


@ensure_infra("persistence", raise_exceptions=False)
async def initialize_fixtures(app: FastAPI):
    """
    initialize fixtures
    """
    # First Library
    import contacts
    from applications import ContactApplication
    from models.contact import Contact

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
            except Exception:
                await application.create_contact(
                    name=code.capitalize(),
                    code=code,
                    description=code,
                    definition={"type": "pydantic", "contact_schema": code},
                )


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

    yield

    # shutdown infrastructure container
    await shutdown_infra(app)

# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
import orjson
from blinker import signal
from fastapi import FastAPI
from strawberry.fastapi.router import GraphQLRouter
from tortoise.transactions import in_transaction

# First Library
from apis import schema
from common.constants import QUEUE_NAME
from helpers.decorators import ensure_infra
from infra import get_infra
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
    # First Library
    import helpers.signals

    infra = get_infra()
    background_scheduler = await infra.background_scheduler()
    queue_infra = await infra.queue()

    # TODO: refact needs to be done
    # make a eventbus manager built with blinker, background scheduler, pubsub, queue
    # and other infrastructures
    async def listen_events():
        try:
            async with queue_infra.channel_pool.acquire() as channel:
                queue = await channel.declare_queue(name=QUEUE_NAME, durable=True)
                message_iterator = queue.iterator()
                async for message in message_iterator:
                    try:
                        data = orjson.loads(message.body)
                        background_scheduler.run_task_in_process_executor(
                            signal(data["signal"]).send_async,
                            kwargs=data["data"],
                        )
                        await message.ack()
                    except Exception as e:
                        await message.reject()
                        print(e)
        except BaseException as e:
            pass

    background_scheduler.run_task_in_process_executor(listen_events)


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

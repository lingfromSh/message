# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
from fastapi import FastAPI
from strawberry.fastapi.router import GraphQLRouter

# First Library
from apis import schema
from infra import initialize_infra
from infra import shutdown_infra


async def initialize_graphql_api(app: FastAPI):
    graphql_router = GraphQLRouter(schema)
    app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])


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

    yield

    # shutdown infrastructure container
    await shutdown_infra(app)

# Third Party Library
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

# First Library
from apis import schema
from lifespan import lifespan

graphql_app = GraphQLRouter(schema)

app = FastAPI(
    title="Message Service",
    description="A general message notification service",
    version="0.0.1",
    lifespan=lifespan,
)

app.include_router(graphql_app, prefix="/graphql")

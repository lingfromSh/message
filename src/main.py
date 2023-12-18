# Third Party Library
from fastapi import FastAPI

# First Library
from lifespan import lifespan

app = FastAPI(
    title="Message Service",
    description="A general message notification service",
    version="0.0.1",
    lifespan=lifespan,
)

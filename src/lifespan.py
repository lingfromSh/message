# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
from fastapi import FastAPI

# First Library
from infra import initialize_infra
from infra import shutdown_infra


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager that ensures that the application is started and stopped
    before and after the context manager.
    """
    # initialize infrastructure container
    await initialize_infra()

    yield

    # shutdown infrastructure container
    await shutdown_infra()

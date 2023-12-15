# Third Party Library
from fastapi import FastAPI

app = FastAPI(
    title="Message API",
    description="A general message notification service",
    version="0.0.1",
)

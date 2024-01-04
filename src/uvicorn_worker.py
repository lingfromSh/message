# Third Party Library
from uvicorn.workers import UvicornWorker


class MessageUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "ws": "websockets",
    }

# Third Party Library
from fastapi import FastAPI
from fastapi import WebSocket

# First Library
from infra import get_infra
from lifespan import lifespan

app = FastAPI(
    title="Message Service",
    description="A general message notification service",
    version="0.0.1",
    lifespan=lifespan,
)


@app.websocket("/websocket/")
async def websocket_endpoint(websocket: WebSocket):
    try:
        infra = get_infra()
        infra_websocket = await infra.websocket()
        connection = await infra_websocket.add_connection(websocket)
        await connection.init()
        await connection.send_welcome()
        await connection.keep_alive()
    finally:
        await infra_websocket.remove_connection(connection)

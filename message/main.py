# Third Party Library
from fastapi import Depends
from fastapi import FastAPI
from fastapi import WebSocket
from message.infra import InfrastructureContainer
from message.infra import get_infra
from message.lifespan import lifespan

app = FastAPI(
    title="Message Service",
    description="A general message notification service",
    version="0.0.1",
    lifespan=lifespan,
)


@app.websocket("/websocket/")
async def websocket_endpoint(
    websocket: WebSocket,
    infra: InfrastructureContainer = Depends(get_infra),
):
    try:
        infra_websocket = await infra.websocket()
        connection = await infra_websocket.add_connection(websocket)
        await connection.init()
        await connection.send_welcome()
        await connection.keep_alive()
    finally:
        await infra_websocket.remove_connection(connection)

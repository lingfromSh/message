import orjson
from sanic import Sanic
from sanic.log import logger

from common.command import setup as setup_command
from common.constants import EXECUTOR_NAME
from configs import ConfigProxy
from setup import setup_app

app = Sanic(
    name=EXECUTOR_NAME,
    strict_slashes=False,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
)
setup_app(app)


@app.websocket("/websocket")
async def handle_websocket(request, ws):
    from apps.endpoint.listeners import register_websocket_endpoint
    from apps.endpoint.listeners import unregister_websocket_endpoint

    con_id = None
    websocket_pool = request.app.ctx.infra.websocket()
    try:
        con_id = await websocket_pool.add_connection(ws)
        logger.debug(f"new connection connected -> {con_id}")
        await websocket_pool.add_listener(con_id, register_websocket_endpoint)
        await websocket_pool.add_close_callback(con_id, unregister_websocket_endpoint)
        await websocket_pool.send(
            con_id, data={"action": "on.connect", "payload": {"connection_id": con_id}}
        )
        await websocket_pool.wait_closed(con_id)
    finally:
        request.app.add_task(websocket_pool.remove_connection(con_id))


@app.before_server_start
async def setup_command_subscribers(app):
    queue = app.ctx.infra.queue()
    async with queue.connection_pool.acquire() as connection:
        await setup_command(app, connection)

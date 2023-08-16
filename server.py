import orjson
from sanic import Sanic

from common.command import setup as setup_command
from common.constants import SERVER_NAME
from configs import ConfigProxy
from setup import setup_app

app = Sanic(
    name=SERVER_NAME,
    strict_slashes=False,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
    log_config={},
)

setup_app(app)


@app.before_server_start
async def setup_command_subscribers(app):
    async with app.ctx.queue.acquire() as connection:
        await setup_command(app, connection)

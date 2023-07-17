import orjson
from sanic import Request
from sanic import Sanic
from sanic.response import json
from sanic.response import text

from common.constants import HEALTHY
from common.constants import SERVER_NAME
from common.constants import UNHEALTHY
from configs import ConfigProxy
from infrastructures.cache import CacheDependency
from infrastructures.mongodb import MongoDBDependency
from infrastructures.queue import QueueDependency
from infrastructures.websocket import WebsocketConnectionPoolDependency

app = Sanic(
    SERVER_NAME,
    strict_slashes=True,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
)
app.ctx.dependencies = set()


@app.before_server_start
async def prepare_cache_dependency(app):
    cache_dependency = CacheDependency(app)
    await cache_dependency.prepare()
    app.ctx.dependencies.add(cache_dependency)


@app.before_server_start
async def prepare_mongodb_dependency(app):
    mongodb_dependency = MongoDBDependency(app)
    await mongodb_dependency.prepare()
    app.ctx.dependencies.add(mongodb_dependency)


@app.before_server_start
async def prepare_queue_dependency(app):
    queue_dependency = QueueDependency(app)
    await queue_dependency.prepare()
    app.ctx.dependencies.add(queue_dependency)


@app.before_server_start
async def prepare_websocket_pool_dependency(app):
    websocket_pool_dependency = WebsocketConnectionPoolDependency(app)
    await websocket_pool_dependency.prepare()
    app.ctx.dependencies.add(websocket_pool_dependency)


@app.get("/")
async def index(request: Request):
    return text("OK")


@app.get("/health/")
async def health(request):
    ret = {}
    for dependency in request.app.ctx.dependencies:
        if await dependency.check():
            ret[dependency.name] = HEALTHY
        else:
            ret[dependency.name] = UNHEALTHY

    return json(ret)


@app.get("/email")
async def email(request):
    from apps.message.providers.email import SMTPEmailMessageProviderModel

    return text("NOT OK")


@app.websocket("/websocket")
async def handle_websocket(request, ws):
    ctx = request.app.ctx
    con_id = ctx.ws_pool.add_connection(ws)
    await ctx.ws_pool.wait_closed(con_id)

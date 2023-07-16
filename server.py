import orjson
from sanic import Sanic
from sanic import Request
from sanic.response import text, json
from configs import ConfigProxy
from infrastructures.cache import CacheDependency
from infrastructures.mongodb import MongoDBDependency
from infrastructures.queue import QueueDependency
from common.constants import SERVER_NAME, HEALTHY, UNHEALTHY


app = Sanic(
    SERVER_NAME,
    strict_slashes=True,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
)


app.ctx.dependencies = set()
app.ctx.dependencies.add(CacheDependency(app))
app.ctx.dependencies.add(MongoDBDependency(app))
app.ctx.dependencies.add(QueueDependency(app))


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

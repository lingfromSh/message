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


@app.get("/email")
async def email(request):
    from apps.message.providers.email import SMTPEmailMessageProviderModel

    provider = SMTPEmailMessageProviderModel
    provider.schema()

    return text("NOT OK")

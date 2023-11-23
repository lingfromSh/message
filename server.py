import orjson
from sanic import Sanic

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

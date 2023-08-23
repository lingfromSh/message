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


@app.before_server_start
def setup_server(app):
    from apps.endpoint.api import bp as endpoint_blueprint
    from apps.message.api import provider_bp, message_bp
    from apps.scheduler.api import bp as scheduler_blueprint

    app.blueprint(endpoint_blueprint)
    app.blueprint(provider_bp)
    app.blueprint(message_bp)
    app.blueprint(scheduler_blueprint)

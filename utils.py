from sanic import Sanic
from common.constants import SERVER_NAME


def get_app():
    return Sanic.get_app(SERVER_NAME)

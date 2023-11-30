import typing

import pymongo
from beanie import Document

from utils import get_app

app = get_app()

cache = app.ctx.infra.cache()


class Endpoint(Document):
    external_id: str
    tags: typing.List[str]
    websockets: typing.List[str]
    emails: typing.List[str]

    class Settings:
        name = "endpoints"
        indexes = [
            pymongo.IndexModel("external_id", unique=True),
            pymongo.IndexModel("tags", sparse=True),
        ]
        keep_nulls = False

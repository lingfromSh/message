import datetime

import pymongo
from beanie import Document
from pydantic import Field


class Provider(Document):
    name: str
    type: str
    code: str
    config: dict

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "providers"
        indexes = [
            "type",
            "code",
            "name",
            ("created_at", pymongo.DESCENDING),
            ("updated_at", pymongo.DESCENDING),
        ]
        use_cache = True

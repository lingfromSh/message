import datetime
import typing

import pymongo
from beanie import Document
from beanie import Link
from pydantic import Field

from models.provider import Provider


class Template(Document):
    # built-in params
    # today - today date string
    # time - current time string

    name: str
    provider: Link[Provider]
    realm: typing.Union[str, bytes, dict, list, int, float, bool]

    is_enabled: bool = Field(default=False)
    # NOTE: some template must be audited, so we need to add a field to control it.
    # NOTE: this flag should only be controlled by provider.
    is_validated: bool = Field(default=True)

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "providers"
        indexes = [
            "name",
            "provider",
            "is_enabled",
            "is_validated",
            ("created_at", pymongo.DESCENDING),
            ("updated_at", pymongo.DESCENDING),
        ]
        use_cache = True

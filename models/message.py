import datetime
import typing

import pymongo
from beanie import Document
from beanie import Link
from pydantic import Field

from apps.message.common.constants import MessageStatus
from models.provider import Provider
from schemas.delivery import DeliveryStatus


class Message(Document):
    provider: Link[Provider]
    realm: typing.Union[str, bytes, dict, list, int, float, bool]
    status: MessageStatus

    result: typing.Optional[typing.List[DeliveryStatus]] = None

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "messages"
        indexes = [
            "provider",
            "status",
            ("created_at", pymongo.DESCENDING),
            ("updated_at", pymongo.DESCENDING),
        ]
        keep_nulls = False

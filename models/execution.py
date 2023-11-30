import datetime
import typing

import pymongo
from beanie import Document
from beanie import Link
from pydantic import Field

from common.constants import ExecutionStatus
from models.message import Message
from models.plan import Plan


class Execution(Document):
    """
    plan run
    """

    plan: Link[Plan]

    result: typing.Optional[typing.List[Message]] = None
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "executions"
        indexes = [
            ("plan", pymongo.ASCENDING),
            ("status", pymongo.ASCENDING),
            ("created_at", pymongo.DESCENDING),
            ("updated_at", pymongo.DESCENDING),
        ]
        keep_nulls = False

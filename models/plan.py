import datetime
import typing

import pymongo
from beanie import Document
from beanie import Link
from pydantic import Field

from common.constants import PlanTriggerType
from models.template import Template


class Plan(Document):
    name: str
    description: str
    tags: typing.List[str]
    type: PlanTriggerType
    trigger: typing.Union[str, int]

    template: Link[Template]

    is_enabled: bool = Field(default=False)

    not_before: typing.Optional[datetime.datetime] = None
    not_after: typing.Optional[datetime.datetime] = None
    last_executed: typing.Optional[datetime.datetime] = None

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "plans"
        indexes = [
            "name",
            "tags",
            "is_enabled",
            ("created_at", pymongo.DESCENDING),
            ("updated_at", pymongo.DESCENDING),
        ]
        keep_nulls = False
        use_cache = True

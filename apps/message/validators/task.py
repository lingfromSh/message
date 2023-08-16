from datetime import datetime
from typing import List
from typing import Optional

from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class FutureSubPlanTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    message: dict

    @field_validator("provider", mode="before")
    def validate_provider(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        elif hasattr(v, "pk"):
            return str(v.pk)
        return str(v)


class FuturePlanTriggersTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    repeat_at: Optional[str] = None
    timer_at: Optional[datetime] = None
    repeat_time: int

    start_time: datetime
    end_time: Optional[datetime] = None

    @model_validator(mode="after")
    def ensure_at(self):
        if self.type == "timer":
            assert self.timer_at is not None
            assert self.repeat_time == 1
        else:
            assert self.repeat_at is not None

        return self


class FuturePlanTask(BaseModel):
    id: str = Field(alias="pk")
    model_config = ConfigDict(from_attributes=True)
    is_enabled: bool
    triggers: List[FuturePlanTriggersTask]
    sub_plans: List[FutureSubPlanTask]

    @field_validator("id", mode="before")
    def validate_id(cls, v) -> str:
        return str(v)


class ImmediateTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    message: str

    @field_validator("provider", "message", mode="before")
    def validate_provider(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        elif hasattr(v, "pk"):
            return str(v.pk)
        return str(v)
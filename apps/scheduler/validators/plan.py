from datetime import datetime
from typing import List
from typing import Optional
from typing import Union

import crontabula
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer
from pydantic import field_validator
from pydantic import model_validator
from umongo.fields import Reference

from apps.scheduler.common.constants import PlanTriggerType
from utils import get_app

from .types import ObjectID

app = get_app()


class PlanTriggerOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    type: PlanTriggerType

    timer_at: Optional[datetime] = None
    repeat_at: Optional[str] = None

    repeat_time: int

    start_time: datetime
    end_time: Optional[datetime] = None

    @field_validator("type", mode="after")
    @classmethod
    def validate_type(cls, v):
        return v.value


class PlanSubPlanOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    provider: Reference
    message: dict

    @field_serializer("provider")
    def serialize_provider(self, provider):
        return str(provider.pk)


class PlanOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: ObjectID = Field(alias="pk")
    name: str
    triggers: List[PlanTriggerOutputModel]
    sub_plans: List[PlanSubPlanOutputModel]

    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class QueryPlanInputModel(BaseModel):
    ids: Optional[List[ObjectID]] = None
    names: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    page: Optional[int] = app.config.API.DEFAULT_PAGE
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE


class PlanTriggerInputModel(PlanTriggerOutputModel):
    @field_validator("repeat_at", mode="after")
    @classmethod
    def validate_repeat_at(cls, v: str):
        try:
            crontabula.parse(v).next
            return v
        except Exception:
            raise ValueError("repeat at is an invalid crontab expression")

    @model_validator(mode="after")
    def ensure_at(self):
        if self.type == PlanTriggerType.TIMER:
            assert self.timer_at is not None
            assert self.repeat_time == 1, "timer's repeat time must be 1"
        else:
            assert self.repeat_at is not None
            assert self.repeat_time >= -1, "repeat's repeat time must greater than -1"
        return self


class PlanSubPlanInputModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    provider: ObjectID
    message: Union[dict, ObjectID]


class CreatePlanInputModel(BaseModel):
    name: str
    triggers: List[PlanTriggerInputModel]
    sub_plans: List[PlanSubPlanInputModel]

    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UpdatePlanInputModel(BaseModel):
    name: Optional[str]
    triggers: Optional[List[PlanTriggerInputModel]]
    sub_plans: Optional[List[PlanSubPlanInputModel]]

    is_enabled: Optional[bool]
    updated_at: datetime = Field(default_factory=datetime.utcnow)

from datetime import datetime
from typing import List
from typing import Optional

import crontabula
from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_validator
from pydantic import model_validator
from umongo.fields import Reference

from apps.message.models import Provider
from apps.scheduler.common.constants import PlanTriggerType
from apps.scheduler.models import Plan

from .types import ObjectID


class PlanTriggerOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    type: PlanTriggerType

    timer_at: Optional[datetime]
    repeat_at: Optional[str]

    repeat_time: int

    start_time: datetime
    end_time: Optional[datetime]

    @field_validator("type", mode="after")
    @classmethod
    def validate_type(cls, v):
        return v.value


class PlanSubPlanOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    provider: Reference
    message: dict


class PlanOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    oid: ObjectID = Field(alias="pk")
    name: str
    triggers: List[PlanTriggerOutputModel]
    sub_plans: List[PlanSubPlanOutputModel]

    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def global_id(self) -> str:
        return self.oid


class CreatePlanTriggerInputModel(PlanTriggerOutputModel):
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


class CreatePlanSubPlanInputModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    provider: Provider
    message: dict


class CreatePlanInputModel(BaseModel):
    name: str
    triggers: List[CreatePlanTriggerInputModel]
    sub_plans: List[CreatePlanSubPlanInputModel]

    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def save(self):
        plan = Plan(**self.model_dump())
        await plan.commit()
        return plan


class DisableEnablePlanInputModel(BaseModel):
    oids: List[ObjectID]


class DestroyPlanInputModel(BaseModel):
    oids: List[ObjectID]

    async def delete(self):
        result = await Plan.collection.delete_many(
            {"_id": {"$in": list(map(ObjectId, self.oids))}}
        )
        return result.deleted_count

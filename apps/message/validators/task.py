from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_serializer
from pydantic import field_validator
from pydantic import model_validator

from apps.message.common.constants import MessageProviderType
from apps.message.validators.types import ObjectID


class ProviderInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectID
    type: MessageProviderType
    code: str
    config: dict = {}

    @field_serializer("type")
    def serialize_type(self, type):
        return type.value


class FutureSubPlanTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: ProviderInfo
    message: dict


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
    id: ObjectID
    model_config = ConfigDict(from_attributes=True)
    is_enabled: bool
    triggers: List[FuturePlanTriggersTask]
    sub_plans: List[FutureSubPlanTask]


class ImmediateTaskProvider(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oid: ObjectID
    type: MessageProviderType
    code: str
    config: Optional[dict] = {}

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        return MessageProviderType(v)

    @field_serializer("type")
    def serialize_type(self, v):
        return v.value


class ImmediateTaskMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oid: ObjectID
    realm: dict


class ImmediateTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: ImmediateTaskProvider
    message: ImmediateTaskMessage

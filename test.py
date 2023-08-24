from datetime import datetime
from pydantic import BaseModel, model_validator, field_serializer, ConfigDict
from typing import Optional, List

import enum
from typing import Annotated

from bson.objectid import ObjectId
from pydantic import PlainSerializer
from pydantic import PlainValidator


class MessageProviderType(str, enum.Enum):
    """
    Providers types
    """

    WEBSOCKET = "websocket"
    EMAIL = "email"
    VOICE_MESSAGE = "voice_message"
    SMS = "sms"


ObjectID = Annotated[
    str, PlainValidator(lambda x: ObjectId(x)), PlainSerializer(lambda x: str(x))
]

a = b'{"id":"64e634a887ca5d9a1512a6cb","is_enabled":true,"triggers":[{"type":"repeat","repeat_at":"0-59/1 * * * *","timer_at":null,"repeat_time":10,"start_time":"2023-08-01T16:39:59Z","end_time":null}],"sub_plans":[{"provider":{"id":"64e55ef3b6354fa1d7f2eb24","type":"websocket","code":"websocket","config":{}},"message":{"connections":["exid:studio:1"],"action":"say.hello","payload":"hello"}}]}'


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


FuturePlanTask.model_validate_json(a).model_dump()

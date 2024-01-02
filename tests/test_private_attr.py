# Third Party Library
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import fields


class Event(BaseModel):
    _event_name: str = fields.PrivateAttr(default_factory=lambda: "Event")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SubEvent(Event):
    name: str
    _event_name: str = "sss"


print(Event())
print(SubEvent._event_name.get_default())
print(SubEvent(name="sub_test")._event_name)

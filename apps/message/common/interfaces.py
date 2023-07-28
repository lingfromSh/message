import ulid
from pydantic import BaseModel
from pydantic import Field


class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(ulid.ULID))


class SendResult(BaseModel):
    provider_id: str
    message: Message

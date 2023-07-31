import ulid
from pydantic import BaseModel
from pydantic import Field

from apps.message.common.constants import MessageStatus
from apps.message.validators.types import ObjectID


class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(ulid.ULID))


class SendResult(BaseModel):
    provider_id: ObjectID
    message: BaseModel
    status: MessageStatus

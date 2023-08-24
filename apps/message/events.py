from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict

from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.validators.types import ObjectID
from common.eventbus import event_handler


class MessageCreateEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    provider_id: ObjectID
    realm: dict
    status: MessageStatus
    created_at: datetime
    updated_at: datetime


@event_handler(MessageCreateEvent)
async def handle_message_create(event: MessageCreateEvent):
    message = Message(
        provider=event.provider_id,
        realm=event.realm,
        status=event.status.value,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
    await message.commit()

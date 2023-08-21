from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict

from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.validators.types import ObjectID
from common.eventbus import CannotResolveError
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
    pass
    # provider = await Provider.find_one({"_id": event.provider_id})
    # if not provider:
    #     raise CannotResolveError

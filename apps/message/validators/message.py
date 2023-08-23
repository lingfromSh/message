from datetime import datetime
from typing import List
from typing import Optional
from typing import Tuple

import orjson
from aio_pika.message import Message as QueueMessage
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from umongo.fields import Reference

from apps.message.common.constants import MessageStatus
from apps.message.common.interfaces import SendResult
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.utils import get_provider
from utils import get_app

from .types import ObjectID

app = get_app()


class SendMessageInputModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider: Provider
    realm: dict

    status: Optional[MessageStatus] = Field(default=MessageStatus.SENDING.value)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def send(self, save=True) -> Tuple[SendResult, Message]:
        provider_cls = get_provider(self.provider.type, self.provider.code)
        if provider_cls.need_configure:
            provider = provider_cls(**self.provider.config)
        else:
            provider = provider_cls()

        validated = provider.validate_message(config=self.realm)

        data = self.model_dump()
        data["realm"] = validated.model_dump()
        data["status"] = MessageStatus.SENDING.value
        data["provider"] = self.provider
        message = Message(**data)

        from apps.message.subscriber import ImmediateMessageTopicSubscriber

        if save:
            await message.commit()

        result = SendResult(
            provider_id=self.provider.pk,
            message=validated,
            status=MessageStatus.SENDING,
        )
        queue_message = ImmediateMessageTopicSubscriber.message_model(
            provider={
                "oid": str(self.provider.pk),
                "type": self.provider.type,
                "code": self.provider.code,
            },
            message={"oid": str(message.pk), "realm": message.realm},
        )
        await ImmediateMessageTopicSubscriber.notify(
            None,
            message=QueueMessage(body=queue_message.model_dump_json().encode()),
        )
        return result, message


class MessageOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    oid: ObjectID = Field(alias="pk")
    provider: Reference
    realm: dict
    status: MessageStatus

    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def global_id(self) -> str:
        return self.oid


class QueryMessageInputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    ids: Optional[List[ObjectID]] = None
    providers: Optional[List[ObjectID]] = None
    status_in: Optional[List[MessageStatus]] = None

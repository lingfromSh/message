from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from umongo.fields import Reference

from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.utils import get_provider

from .types import ObjectID


class SendMessageInputModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider: Provider
    realm: dict

    status: Optional[MessageStatus] = Field(default=MessageStatus.SENDING.value)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def send(self):
        provider_cls = get_provider(self.provider.type, self.provider.code)
        if provider_cls.need_configure:
            provider = provider_cls(**self.provider.config)
        else:
            provider = provider_cls()
        validated = provider.validate_message(config=self.realm)
        result = await provider.send(provider_id=self.provider.pk, message=validated)
        data = self.model_dump()
        data["realm"] = validated.model_dump()
        data["status"] = result.status.value
        data["provider"] = self.provider
        message = Message(**data)
        await message.commit()
        return message


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

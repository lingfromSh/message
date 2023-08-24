from datetime import datetime
from typing import Optional
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_serializer
from umongo.fields import Reference

from apps.message.common.constants import MessageStatus
from apps.message.models import Provider
from utils import get_app

from .types import ObjectID

app = get_app()


class SendMessageInputModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider: ObjectID
    realm: dict

    status: Optional[MessageStatus] = Field(default=MessageStatus.SENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("status")
    def serialize_status(self, status):
        return status.value


class MessageOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: ObjectID = Field(alias="pk")
    provider: Reference
    realm: dict
    status: MessageStatus

    created_at: datetime
    updated_at: datetime

    @field_serializer("provider")
    def serialize_provider(self, provider):
        return provider.pk


class QueryMessageInputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    ids: Optional[List[ObjectID]] = None
    providers: Optional[List[ObjectID]] = None
    status_in: Optional[List[MessageStatus]] = None

    page: Optional[int] = app.config.API.DEFAULT_PAGE
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE

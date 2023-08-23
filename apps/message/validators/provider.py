from datetime import datetime
from typing import Annotated
from typing import List
from typing import Optional

from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import WrapSerializer
from pydantic import field_serializer
from pydantic import constr
from pydantic import model_validator
from typing_extensions import Annotated

from apps.message.common.constants import MessageProviderType
from apps.message.models import Provider
from apps.message.utils import get_provider
from utils import get_app

from .types import ObjectID

app = get_app()


def ser_enum(v, nxt):
    return nxt(v.value)


WrappedMessageProviderType = Annotated[MessageProviderType, WrapSerializer(ser_enum)]


class EnsureProviderMixin:
    @model_validator(mode="after")
    def ensure_provider(self):
        get_provider(self.type, self.code)
        return self


class CheckConfigMixin:
    @model_validator(mode="after")
    def check_config(self):
        config = self.config

        provider = get_provider(self.type, self.code)

        if not provider.need_configure:
            # clear config
            self.config = None
        else:
            provider.validate_config(config)

        return self


class CreateProviderInputModel(EnsureProviderMixin, CheckConfigMixin, BaseModel):
    type: WrappedMessageProviderType
    code: constr(to_lower=True, max_length=32)
    name: constr(max_length=1024)
    config: Optional[dict] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    async def save(self):
        provider = Provider(**self.model_dump())
        await provider.commit()
        return provider


class UpdateProviderInputModel(EnsureProviderMixin, CheckConfigMixin, BaseModel):
    type: Optional[WrappedMessageProviderType] = None
    code: Optional[constr(to_lower=True, max_length=32)] = None
    name: Optional[constr(max_length=1024)] = None
    config: Optional[dict] = None

    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DestroyProviderInputModel(BaseModel):
    oids: List[ObjectID]

    async def delete(self):
        result = await Provider.collection.delete_many(
            {"_id": {"$in": list(map(ObjectId, self.oids))}}
        )
        return result.deleted_count


class ProviderOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectID = Field(alias="pk")
    type: MessageProviderType
    code: constr(to_lower=True, max_length=32)
    name: constr(max_length=1024)
    config: Optional[dict]

    created_at: datetime
    updated_at: datetime

    @field_serializer("type")
    def serialize_type(self, type):
        return type.value


class QueryProviderInputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ids: Optional[List[str]] = None
    types: Optional[List[MessageProviderType]] = None
    codes: Optional[List[str]] = None
    names: Optional[List[str]] = None
    page: Optional[int] = app.config.API.DEFAULT_PAGE
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE

from typing import Optional, List

from datetime import datetime, UTC
from pydantic import BaseModel
from pydantic import Field
from apps.message.validators.provider import ProviderOutputModel
from apps.template.validators.types import ObjectID
from utils import get_app

app = get_app()


class QueryTemplateInputModel(BaseModel):
    names: Optional[List][str] = None
    providers: Optional[List][ObjectID] = None
    is_enabled: Optional[bool] = None

    page: Optional[int] = app.config.API.DEFAULT_PAGE
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE


class CreateTemplateInputModel(BaseModel):
    name: str
    provider: ObjectID

    content: dict
    is_enabled: bool = True

    created_at: datetime = Field(default_factory=datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=datetime.now(tz=UTC))


class UpdateTemplateInputModel(BaseModel):
    name: Optional[str]
    provider: Optional[ObjectID]
    content: dict
    is_enabled: bool

    updated_at = Field(default_factory=datetime.now(tz=UTC))


class TemplateOutputModel(BaseModel):
    id: ObjectID = Field(alias="pk")
    name: str
    provider: ProviderOutputModel
    content: dict

    created_at: datetime
    updated_at: datetime

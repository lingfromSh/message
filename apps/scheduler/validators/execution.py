from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from umongo.fields import Reference

from apps.scheduler.common.constants import PlanExecutionStatus
from utils import get_app
from .types import ObjectID


app = get_app()


class PlanExecutionOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: ObjectID = Field(alias="pk")
    plan: Reference
    status: PlanExecutionStatus
    reason: Optional[List[str]]

    time_to_execute: datetime
    created_at: datetime
    updated_at: datetime


class QueryPlanExecutionInputModel(BaseModel):
    ids: Optional[List[ObjectID]] = None
    plans: Optional[List[ObjectID]] = None
    page: Optional[int] = app.config.API.DEFAULT_PAGE
    page_size: Optional[int] = app.config.API.DEFAULT_PAGE_SIZE

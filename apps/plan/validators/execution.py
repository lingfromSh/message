from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from umongo.fields import Reference

from apps.plan.common.constants import PlanExecutionStatus

from .types import ObjectID


class PlanExecutionOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    oid: ObjectID = Field(alias="pk")
    plan: Reference
    status: PlanExecutionStatus
    reason: Optional[List[str]]

    time_to_execute: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def global_id(self) -> str:
        return self.oid

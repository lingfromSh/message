import dataclasses
from datetime import datetime
from typing import List
from typing import Optional

import strawberry
from bson.objectid import ObjectId

from apps.message.models import Provider
from apps.scheduler.common.constants import PlanTriggerType
from apps.scheduler.validators.plan import CreatePlanInputModel
from apps.scheduler.validators.plan import DestroyPlanInputModel
from infrastructures.graphql import ObjectID


@strawberry.input
class PlanTriggerInput:
    type: strawberry.enum(PlanTriggerType)
    timer_at: Optional[datetime] = None
    repeat_at: Optional[str] = None
    repeat_time: int

    start_time: datetime
    end_time: Optional[datetime] = None


@strawberry.input
class PlanSubPlanInput:
    provider: ObjectID
    message: strawberry.scalars.JSON


@strawberry.input
class CreatePlanInput:
    name: str
    triggers: List[PlanTriggerInput]
    sub_plans: List[PlanSubPlanInput]

    is_enabled: bool = True

    async def to_pydantic(self) -> CreatePlanInputModel:
        data = dataclasses.asdict(self)
        for sub_plan in data["sub_plans"]:
            if not isinstance(sub_plan, dict):
                continue
            provider = await Provider.find_one(
                {"_id": ObjectId(sub_plan.get("provider"))}
            )
            sub_plan["provider"] = provider
        return CreatePlanInputModel.model_validate(data)


@strawberry.input
class DestroyPlanInput:
    oids: List[ObjectID]

    def to_pydantic(self) -> DestroyPlanInputModel:
        data = dataclasses.asdict(self)
        return DestroyPlanInputModel.model_validate(data)

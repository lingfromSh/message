from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict

from apps.scheduler.common.constants import PlanExecutionStatus
from apps.scheduler.models import Plan
from apps.scheduler.models import PlanExecution
from apps.scheduler.validators.types import ObjectID
from common.eventbus import CannotResolveError
from common.eventbus import event_handler


class PlanExecutionCreateEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    plan_id: ObjectID
    status: PlanExecutionStatus
    time_to_execute: datetime
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@event_handler(PlanExecutionCreateEvent)
async def handle_plan_execution_create(event: PlanExecutionCreateEvent):
    plan = await Plan.find_one({"_id": event.plan_id})
    if not plan:
        raise CannotResolveError

    try:
        execution = PlanExecution(
            plan=plan,
            status=event.status.value,
            time_to_execute=event.time_to_execute,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )

        if event.reason is not None:
            execution.reason = event.reason

        await execution.commit()
    except Exception:
        raise CannotResolveError


class PlanTriggerRepeatTimeDecreaseEvent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    plan_id: ObjectID
    by: int = 1


@event_handler(PlanTriggerRepeatTimeDecreaseEvent)
async def handle_plan_trigger_repeat_time_decrease(
    event: PlanTriggerRepeatTimeDecreaseEvent,
):
    plan = await Plan.find_one({"_id": event.plan_id})
    if not plan:
        raise CannotResolveError

    try:
        for trigger in plan.triggers:
            if trigger.repeat_time > 0:
                trigger.repeat_time -= 1
        await plan.commit()
    except Exception:
        raise CannotResolveError

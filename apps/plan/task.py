from datetime import datetime
from datetime import timedelta
from typing import List

import orjson
from aio_pika import DeliveryMode
from aio_pika.message import Message
from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from sanic.log import logger

from apps.plan.models import Plan
from apps.plan.models import PlanExecution
from apps.plan.common.constants import PlanTriggerType, PlanExecutionStatus
from apps.message.subscriber import InQueueMessageTopicSubscriber
from common.command import publish
from utils import get_app


class FutureSubPlanTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    message: dict

    @field_validator("provider", mode="before")
    def validate_provider(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        elif hasattr(v, "pk"):
            return str(v.pk)
        return str(v)


class FuturePlanTriggersTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    at: datetime


class FuturePlanTask(BaseModel):
    id: str = Field(alias="pk")
    model_config = ConfigDict(from_attributes=True)
    is_enabled: bool
    triggers: List[FuturePlanTriggersTask]
    sub_plans: List[FutureSubPlanTask]

    @field_validator("id", mode="before")
    def validate_id(cls, v) -> str:
        return str(v)


async def enqueue_future_task():
    logger.info("start enqueueing tasks")
    now = datetime.utcnow()
    app = get_app()

    async with app.shared_ctx.queue.acquire() as connection:
        async for plan in Plan.find(
            {
                "triggers.at": {
                    "$gte": now + timedelta(minutes=15),
                    "$lte": now + timedelta(minutes=45),
                },
                "is_enabled": True,
                "$or": [
                    {"triggers.repeat_time": -1},
                    {"triggers.repeat_time": {"$gt": 0}},
                ],
            }
        ):
            logger.info(f"Add task {plan}")

            # TODO: 增加一个任务，长时间没有变化的任务置为失败
            execution = PlanExecution(
                plan=plan,
                status=PlanExecutionStatus.IN_QUEUE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await execution.commit()

            await publish(
                connection,
                message=Message(
                    headers={"execution_id": str(execution.pk)},
                    body=orjson.dumps(FuturePlanTask.model_validate(plan).model_dump()),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                topic=InQueueMessageTopicSubscriber.topic,
            )

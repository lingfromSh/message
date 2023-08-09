from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import List
from typing import Optional

import crontabula
import orjson
from aio_pika import DeliveryMode
from aio_pika.message import Message
from bson.objectid import ObjectId
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from sanic.log import logger

from apps.message.subscriber import InQueueMessageTopicSubscriber
from apps.plan.common.constants import PlanTriggerType
from apps.plan.models import Plan
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
    repeat_at: Optional[str] = None
    timer_at: Optional[datetime] = None
    repeat_time: int

    start_time: datetime
    end_time: Optional[datetime] = None

    @model_validator(mode="after")
    def ensure_at(self):
        if self.type == "timer":
            assert self.timer_at is not None
            assert self.repeat_time == 1
        else:
            assert self.repeat_at is not None

        return self


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
    now = datetime.now(tz=UTC)
    app = get_app()
    rlock_name = "plan.{pk}.lock"
    interval = 5 * 60

    async def publish_task(c, p, t):
        message = Message(
            body=orjson.dumps(FuturePlanTask.model_validate(p).model_dump()),
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await InQueueMessageTopicSubscriber.delay_notify(
            c,
            message=message,
            delay=(t - datetime.now(tz=UTC)).total_seconds(),
        )
        logger.info(f"Enqueue task {message.message_id}")

    async with app.ctx.queue.acquire() as connection:
        plans = []
        async for plan in Plan.find(
            # start_time 小于等于现在
            # end_time 大于等于30分钟以后或者无限制
            # is_enabled = True
            # 要么是timer类型, timer_at在30分钟以内, repeat_time大于0
            # 或者是repeat类型
            {
                "$and": [
                    {"triggers.start_time": {"$lte": now}},
                    {"is_enabled": True},
                    {
                        "$or": [
                            {"triggers.end_time": None},
                            {
                                "triggers.end_time": {
                                    "$gte": now + timedelta(seconds=interval)
                                }
                            },
                        ]
                    },
                    {
                        "$or": [
                            {
                                "triggers.type": PlanTriggerType.TIMER.value,
                                "triggers.timer_at": {
                                    "$gte": now,
                                    "$lte": now + timedelta(seconds=interval),
                                },
                                "triggers.repeat_time": {"$gt": 0},
                            },
                            {
                                "triggers.type": PlanTriggerType.REPEAT.value,
                                "triggers.repeat_at": {"$exists": True},
                                "$or": [
                                    {"triggers.repeat_time": {"$gt": 0}},
                                    {"triggers.repeat_time": -1},
                                ],
                            },
                        ]
                    },
                ],
            }
        ):
            logger.info(f"get candidate plan: {plan.pk}")
            lock = app.ctx.cache.lock(
                name=rlock_name.format(pk=str(plan.pk)),
                timeout=interval,
            )
            if not await lock.acquire(blocking=False):
                logger.info(f"plan: {plan.pk} is processed, then skip it")
                continue

            # TODO: 增加一个任务，长时间没有变化的任务置为失败
            try:
                time_to_execute_count = 0
                for trigger in plan.triggers:
                    if now < trigger.start_time:
                        continue

                    if trigger.end_time is not None and now > trigger.end_time:
                        continue

                    trigger_type = PlanTriggerType(trigger.type)
                    if trigger_type == PlanTriggerType.TIMER:
                        time_to_execute = trigger.timer_at
                        await publish_task(connection, plan, time_to_execute)
                        time_to_execute_count += 1
                    else:
                        try:
                            cron = crontabula.parse(trigger.repeat_at)
                            start_time = max(
                                now, trigger.last_trigger or trigger.start_time
                            )
                            for time_to_execute in cron.date_times(start=start_time):
                                time_to_execute = time_to_execute.astimezone(UTC)
                                # only compute execution in this duration
                                if time_to_execute > now + timedelta(seconds=interval):
                                    break

                                # skip executing after end time
                                if (
                                    trigger.end_time is not None
                                    and time_to_execute > trigger.end_time
                                ):
                                    break

                                trigger.last_trigger = time_to_execute
                                await publish_task(connection, plan, time_to_execute)
                                time_to_execute_count += 1
                            plans.append(plan)
                        except Exception:
                            logger.exception("Invalid cron expr")
                            continue

                logger.info(f"add future execution: {time_to_execute_count}")
            except Exception:
                logger.exception("got invalid plan")
                await lock.release()

            for plan in plans:
                await plan.commit()

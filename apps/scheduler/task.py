import math
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import crontabula
from sanic.log import logger

from apps.message.models import Provider
from apps.scheduler.common.constants import PlanTriggerType
from apps.scheduler.models import Plan
from apps.scheduler.utils import publish_task
from utils import get_app


async def enqueue_future_task():
    # logger.info("start enqueueing tasks")
    now = datetime.now(tz=UTC)
    app = get_app()
    rlock_name = "plan.{pk}.lock"
    interval = 5 * 60

    # start_time 小于等于现在
    # end_time 大于等于30分钟以后或者无限制
    # is_enabled = True
    # 要么是timer类型, timer_at在30分钟以内, repeat_time大于0
    # 或者是repeat类型
    start = now + timedelta(seconds=interval)
    end = now + timedelta(seconds=interval * 2)
    condition = {
        "$and": [
            {"triggers.start_time": {"$lte": start}},
            {"is_enabled": True},
            {
                "$or": [
                    {"triggers.end_time": None},
                    {"triggers.end_time": {"$gte": end}},
                ]
            },
            {
                "$or": [
                    {
                        "triggers.type": PlanTriggerType.TIMER.value,
                        "triggers.timer_at": {
                            "$gte": start,
                            "$lte": end,
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
            {"sub_plans": {"$exists": True, "$ne": []}},
        ],
    }

    providers = {provider.pk: provider async for provider in Provider.find()}

    cache = app.ctx.infra.cache()
    queue = app.ctx.infra.queue()
    async with queue.connection_pool.acquire() as connection:
        total_plan_count = await Plan.count_documents(condition)
        limit = math.ceil(total_plan_count / app.ctx.workers)
        skip = app.ctx.worker_id * limit
        async for plan in Plan.find(condition).limit(limit).skip(skip):
            lock = cache.lock(
                name=rlock_name.format(pk=str(plan.pk)),
                timeout=interval * 2,
            )
            if not await lock.acquire(blocking=False):
                # logger.info(f"plan: {plan.pk} is processed, then skip it")
                continue

            # TODO: 增加一个任务，长时间没有变化的任务置为失败

            plan_dict = {
                "id": plan.pk,
                "is_enabled": plan.is_enabled,
                "triggers": [
                    {
                        "type": t.type,
                        "repeat_at": t.repeat_at,
                        "timer_at": t.timer_at,
                        "repeat_time": t.repeat_time,
                        "start_time": t.start_time,
                        "end_time": t.end_time,
                    }
                    for t in plan.triggers
                ],
                "sub_plans": [
                    {
                        "provider": {
                            "id": sub_plan.provider.pk,
                            "type": providers.get(sub_plan.provider.pk).type,
                            "code": providers.get(sub_plan.provider.pk).code,
                            "config": providers.get(sub_plan.provider.pk).config or {},
                        },
                        "message": sub_plan.message,
                    }
                    for sub_plan in plan.sub_plans
                ],
            }

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
                        await publish_task(connection, plan_dict, time_to_execute)
                        time_to_execute_count += 1
                    else:
                        try:
                            cron = crontabula.parse(trigger.repeat_at)
                            start_time = max(
                                start, trigger.last_trigger or trigger.start_time
                            )
                            for time_to_execute in cron.date_times(start=start_time):
                                time_to_execute = time_to_execute.astimezone(UTC)
                                # only compute execution in this duration
                                if time_to_execute > end:
                                    break

                                # skip executing after end time
                                if (
                                    trigger.end_time is not None
                                    and time_to_execute > trigger.end_time
                                ):
                                    break

                                trigger.last_trigger = time_to_execute
                                await publish_task(
                                    connection, plan_dict, time_to_execute
                                )
                                time_to_execute_count += 1
                        except Exception:
                            logger.exception("Invalid cron expr")
                            continue

                logger.info(f"add future execution: {time_to_execute_count}")
            except Exception:
                logger.exception("got invalid plan")
                await lock.release()

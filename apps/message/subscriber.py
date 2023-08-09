import asyncio
from datetime import datetime

import orjson
from aio_pika.abc import AbstractIncomingMessage
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.log import logger

from apps.message.models import Provider
from apps.message.models import Message
from apps.message.validators.message import SendMessageInputModel
from common.command import TopicSubscriber


class InQueueMessageTopicSubscriber(TopicSubscriber):
    topic: str = "inqueue.message"
    durable = True
    deadletter = True

    @classmethod
    def get_lock(cls, app, message):
        return app.ctx.cache.lock(f"inqueue.message.handle.{message.message_id}.lock")

    @classmethod
    async def is_message_processed(cls, app, message) -> bool:
        return not await cls.get_lock(app, message).acquire(blocking=False)

    @classmethod
    async def redo(cls, app, message):
        try:
            await cls.get_lock(app, message).release()
        except Exception:
            pass

    @classmethod
    async def handle(
        cls,
        app: Sanic,
        message: AbstractIncomingMessage,
        semaphore: asyncio.Semaphore = None,
        context: dict = {},
    ):
        from apps.plan.task import FuturePlanTask

        async with message.process(ignore_processed=True):
            logger.info(f"got message: {message.message_id}")

            finished_sub_plans = 0
            db_messages = []
            try:
                body = orjson.loads(message.body)
                body["pk"] = body.get("id")
                task = FuturePlanTask.model_validate(body)
                errors = []
                for sub_plan in task.sub_plans:
                    try:
                        if ObjectId(sub_plan.provider) in context["providers"]:
                            db_provider = context["providers"][
                                ObjectId(sub_plan.provider)
                            ]
                        else:
                            db_provider = await Provider.find_one(
                                {"_id": ObjectId(sub_plan.provider)}
                            )
                    except Exception:
                        logger.info(
                            f"provider: {sub_plan.provider} does not exist - skip this sub plan"
                        )
                        continue

                    try:
                        model = SendMessageInputModel(
                            provider=db_provider,
                            realm=sub_plan.message,
                        )
                        _, db_message = await model.send(save=False)
                        db_messages.append(db_message)
                        finished_sub_plans += 1
                    except Exception:
                        logger.debug("sub plan is not valid - skip this sub plan")
                        continue

                await Message.collection.insert_many(db_messages)
            except Exception:
                # validation error or send error
                pass

            try:
                # TODO: 通过队列解耦合操作
                from apps.plan.common.constants import PlanExecutionStatus
                from apps.plan.models import Plan
                from apps.plan.models import PlanExecution

                execution = PlanExecution(
                    plan=ObjectId(task.id),
                    status=PlanExecutionStatus.IN_QUEUE.value,
                    time_to_execute=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                if finished_sub_plans == 0:
                    execution.status = PlanExecutionStatus.FAILED.value
                    execution.reason = errors
                    await message.reject()
                else:
                    execution.status = PlanExecutionStatus.SUCCEEDED.value
                    await message.ack()

                await execution.commit()

                if ObjectId(task.id) in context["plans"]:
                    plan = context["plans"][ObjectId(task.id)]
                else:
                    plan = await Plan.find_one({"_id": ObjectId(task.id)})
                for trigger in plan.triggers:
                    if trigger.repeat_time > 0:
                        trigger.repeat_time -= 1
                await plan.commit()

            except Exception as err:
                logger.exception(str(err))
                logger.info("invalid future message to send")
                try:
                    await message.reject()
                except Exception:
                    ...

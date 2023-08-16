import asyncio
from datetime import datetime

import orjson
from aio_pika.abc import AbstractIncomingMessage
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.log import logger

from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.validators.message import SendMessageInputModel
from apps.message.validators.task import FuturePlanTask
from apps.message.validators.task import ImmediateTask
from common.command import TopicSubscriber


class InQueueMessageTopicSubscriber(TopicSubscriber):
    topic: str = "inqueue.message"
    durable = True
    deadletter = True

    message_model = FuturePlanTask

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
                        db_messages.append(db_message.to_mongo())
                        finished_sub_plans += 1
                    except Exception:
                        logger.exception("sub plan is not valid - skip this sub plan")
                        continue

                await Message.collection.insert_many(db_messages)
            except Exception as err:
                # validation error or send error
                pass

            try:
                # TODO: 通过队列解耦合操作
                from apps.scheduler.common.constants import PlanExecutionStatus
                from apps.scheduler.models import Plan
                from apps.scheduler.models import PlanExecution

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

            except Exception:
                logger.info("invalid future message to send")
                try:
                    await message.reject()
                except Exception:
                    ...


class ImmediateMessageTopicSubscriber(TopicSubscriber):
    topic: str = "immediate.message"
    durable = True
    deadletter = False

    message_model = ImmediateTask

    @classmethod
    async def handle(
        cls,
        app: Sanic,
        message: AbstractIncomingMessage,
        semaphore: asyncio.Semaphore = None,
        context: dict = {},
    ):
        async with message.process(ignore_processed=True):
            logger.info(f"got message: {message.message_id}")

            try:
                data = orjson.loads(message.body)
                task = ImmediateTask.model_validate(data)
            except orjson.JSONDecodeError:
                return

            try:
                if ObjectId(task.provider) in context["providers"]:
                    db_provider = context["providers"][ObjectId(task.provider)]
                else:
                    db_provider = await Provider.find_one(
                        {"_id": ObjectId(task.provider)}
                    )
            except Exception:
                logger.info(
                    f"provider: {task.provider} does not exist - skip this task"
                )
                return

            try:
                if ObjectId(task.message) in context.get("messages", {}):
                    db_message = context["messages"][ObjectId[task.message]]
                else:
                    db_message = await Message.find_one({"_id": ObjectId(task.message)})

                if db_message.status == MessageStatus.SUCCEEDED.value:
                    logger.info(f"message: {task.message} was sent - skip this task")
                    return

            except Exception:
                logger.info(f"message: {task.message} does not exist - skip this task")
                return

            try:
                model = SendMessageInputModel(
                    provider=db_provider,
                    realm=db_message.realm,
                )
                result, message = await model.send(save=False)
                if result.status == MessageStatus.SUCCEEDED:
                    db_message.status = message.status
                    db_message.updated_at = message.updated_at
                    await db_message.commit()
            except Exception:
                logger.exception("message is not valid - skip this task")

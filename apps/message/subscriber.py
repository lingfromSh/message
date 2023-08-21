import asyncio
from datetime import UTC
from datetime import datetime

import orjson
from aio_pika.abc import AbstractIncomingMessage
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.log import logger

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.events import MessageCreateEvent
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.utils import get_provider
from apps.message.validators.message import SendMessageInputModel
from apps.message.validators.task import FuturePlanTask
from apps.message.validators.task import ImmediateTask
from apps.scheduler.events import PlanExecutionCreateEvent
from apps.scheduler.events import PlanTriggerRepeatTimeDecreaseEvent
from common.command import TopicSubscriber
from common.constants import EXECUTOR_NAME
from common.eventbus import EventBusTopicSubscriber


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
            # logger.info(f"got message: {message.message_id}")
            events = []
            finished_sub_plans = 0
            try:
                task = FuturePlanTask.model_validate_json(message.body)
                errors = []
                for sub_plan in task.sub_plans:
                    # try:
                    #     if ObjectId(sub_plan.provider) in context.get("providers", {}):
                    #         db_provider = context["providers"][
                    #             ObjectId(sub_plan.provider)
                    #         ]
                    #     else:
                    #         db_provider = await Provider.find_one(
                    #             {"_id": ObjectId(sub_plan.provider)}
                    #         )
                    # except Exception:
                    #     logger.info(
                    #         f"provider: {sub_plan.provider} does not exist - skip this sub plan"
                    #     )
                    #     continue

                    try:
                        provider = get_provider("websocket", "websocket")(
                            **{}
                            # **(db_provider.config or {})
                        )
                        validated = provider.validate_message(config=sub_plan.message)

                        result = await provider.send(sub_plan.provider, validated)

                        events.append(
                            MessageCreateEvent(
                                provider_id=sub_plan.provider,
                                realm=sub_plan.message,
                                status=result.status.value,
                                created_at=datetime.now(tz=UTC),
                                updated_at=datetime.now(tz=UTC),
                            )
                        )

                        finished_sub_plans += 1
                    except Exception:
                        logger.exception("sub plan is not valid - skip this sub plan")
                        continue

            except Exception as err:
                # validation error or send error
                logger.warning(f"failed to send or save message: {err}")

            try:
                # TODO: 通过队列解耦合操作
                from apps.scheduler.common.constants import PlanExecutionStatus

                execution = dict(
                    plan_id=task.id,
                    status=PlanExecutionStatus.IN_QUEUE,
                    time_to_execute=datetime.now(tz=UTC),
                    created_at=datetime.now(tz=UTC),
                    updated_at=datetime.now(tz=UTC),
                )

                if finished_sub_plans == 0:
                    execution["status"] = PlanExecutionStatus.FAILED
                    execution["reason"] = errors
                else:
                    execution["status"] = PlanExecutionStatus.SUCCEEDED

                events.append(PlanExecutionCreateEvent(**execution))

                # if ObjectId(task.id) in context.get("plans", {}):
                #     plan = context["plans"][ObjectId(task.id)]
                # else:
                #     plan = await Plan.find_one({"_id": ObjectId(task.id)})
                # for trigger in plan.triggers:
                #     if trigger.repeat_time > 0:
                #         trigger.repeat_time -= 1
                # await plan.commit()

                events.append(PlanTriggerRepeatTimeDecreaseEvent(plan_id=task.id))

                for event in events:
                    app.add_task(
                        EventBusTopicSubscriber.notify(None, message=event.to_message())
                    )

            except Exception as err:
                logger.info("invalid future message to send")
                await message.reject()


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
                task = ImmediateTask.model_validate_json(message.body)
            except Exception:
                return

            try:
                provider = get_provider(task.provider.type, task.provider.code)(
                    **task.provider.config
                )
                validated = provider.validate_message(config=task.message.realm)

                result = await provider.send(task.provider.oid, validated)
                
                if result.status == MessageStatus.SUCCEEDED:
                    await Message.collection.update_one(
                        {"_id": ObjectId(task.message.oid)},
                        {
                            "$set": {
                                "status": result.status.value,
                                "updated_at": datetime.now(tz=UTC),
                            }
                        },
                    )
                logger.info("finished to send message")
            except Exception:
                logger.exception("message is not valid - skip this task")

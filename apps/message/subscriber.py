import asyncio
from datetime import UTC
from datetime import datetime

from aio_pika.abc import AbstractIncomingMessage
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.log import logger

from apps.message.common.constants import MessageStatus
from apps.message.events import MessageCreateEvent
from apps.message.models import Message
from apps.message.utils import get_provider
from apps.message.validators.task import FuturePlanTask
from apps.message.validators.task import ImmediateTask
from apps.scheduler.events import PlanExecutionCreateEvent
from apps.scheduler.events import PlanTriggerRepeatTimeDecreaseEvent
from common.command import TopicSubscriber
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
                    try:
                        provider = get_provider(
                            sub_plan.provider.type, sub_plan.provider.code
                        )(**sub_plan.provider.config)
                        validated = provider.validate_message(config=sub_plan.message)

                        result = await provider.send(sub_plan.provider.id, validated)

                        events.append(
                            MessageCreateEvent(
                                provider_id=sub_plan.provider.id,
                                realm=sub_plan.message,
                                status=result.status.value,
                                created_at=datetime.now(tz=UTC),
                                updated_at=datetime.now(tz=UTC),
                            )
                        )

                        finished_sub_plans += 1
                    except Exception as err:
                        logger.warning("sub plan is not valid - skip this sub plan")
                        break

            except Exception:
                # validation error or send error
                logger.warning(f"failed to send or save message")

            try:
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
                events.append(PlanTriggerRepeatTimeDecreaseEvent(plan_id=task.id))

                for event in events:
                    app.add_task(
                        EventBusTopicSubscriber.notify(message=event.to_message())
                    )

            except Exception:
                logger.info("invalid future message to send")


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
                    **(task.provider.config or {})
                )
                validated = provider.validate_message(config=task.message.realm)

                result = await provider.send(task.provider.id, validated)

                if result.status == MessageStatus.SUCCEEDED:
                    await Message.collection.update_one(
                        {"_id": ObjectId(task.message.id)},
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

import asyncio
import orjson
from aio_pika.abc import AbstractIncomingMessage
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.log import logger

from apps.message.models import Provider
from apps.message.validators.message import SendMessageInputModel
from apps.plan.models import PlanExecution
from common.command import TopicSubscriber


class InQueueMessageTopicSubscriber(TopicSubscriber):
    topic: str = "inqueue.message"
    durable = True

    @classmethod
    async def is_message_processed(cls, app, message) -> bool:
        return await app.shared_ctx.cache.get(message.message_id) is not None

    @classmethod
    async def set(cls, app, message):
        await app.shared_ctx.cache.set(message.message_id, 1)

    @classmethod
    async def unset(cls, app, message):
        await app.shared_ctx.cache.delete(message.message_id)

    @classmethod
    async def handle(
        cls, app: Sanic, semaphore: asyncio.Semaphore, message: AbstractIncomingMessage
    ):
        from apps.plan.task import FuturePlanTask

        await semaphore.acquire()
        async with message.process(reject_on_redelivered=True, ignore_processed=True):
            logger.info(f"got message: {message.message_id}")

            if await cls.is_message_processed(app, message=message):
                logger.info(f"message: {message.message_id} is processed.")

            await cls.set(app, message=message)
            body = orjson.loads(message.body)
            try:
                body["pk"] = body.get("id")
                task = FuturePlanTask.model_validate(body)
                errors = []
                finished_sub_plans = 0
                for sub_plan in task.sub_plans:
                    try:
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
                        await model.send()
                        finished_sub_plans += 1
                    except Exception:
                        logger.debug("sub plan is not valid - skip this sub plan")
                        continue

                # TODO: 通过队列解耦合操作
                from apps.plan.models import PlanExecution
                from apps.plan.common.constants import PlanExecutionStatus

                execution = await PlanExecution.find_one(
                    {"_id": ObjectId(message.headers.get("execution_id", ""))}
                )

                if finished_sub_plans == 0:
                    execution.status = PlanExecutionStatus.FAILED.value
                    execution.reason = errors
                    await message.reject()
                else:
                    execution.status = PlanExecutionStatus.SUCCEEDED.value
                    await message.ack()

                await execution.commit()

            except Exception:
                await message.reject()
                await cls.unset(app, message=message)
                raise
            finally:
                semaphore.release()

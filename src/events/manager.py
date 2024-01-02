# Standard Library
import asyncio

# Third Party Library
from pydantic import ValidationError

# First Library
from common.constants import QUEUE_NAME
from infra import get_infra

# Local Folder
from .base import EventSource


class EventBus:
    TERMINATE = "terminate#"

    def __init__(self, getter):
        self.getter = getter
        self.infra = get_infra()
        self.simple_event_task = None
        self.shared_event_task = None

    async def consume_simple_event(self):
        # TODO: build a message generator to shutdown gracefully
        queue = await self.infra.queue()

        try:
            async with queue.channel_pool.acquire() as channel:
                queue = await channel.declare_queue(name=QUEUE_NAME, durable=True)
                async with queue.iterator() as queue_iterator:
                    async for message in queue_iterator:
                        try:
                            event_source = EventSource.model_validate_json(message.body)
                            await event_source.payload.handle(
                                event=event_source.payload, event_source=event_source
                            )
                        except ValidationError:
                            await message.reject()
                        except Exception as err:
                            # TODO: retry
                            await message.reject()
        except Exception:
            pass

    async def consume_shared_event(self):
        # TODO: build a message generator to shutdown gracefully
        cache = await self.infra.cache()
        async with cache.redis.pubsub() as pubsub:
            await pubsub.subscribe("shared_events")
            async for message in pubsub.listen():
                data = message["data"]
                try:
                    event_source = EventSource.model_validate_json(data)
                    await event_source.payload.handle(
                        event=event_source.payload, event_source=event_source
                    )
                except ValidationError as err:
                    pass
                except Exception as err:
                    # TODO: retry
                    print(err)

    async def startup(self):
        self.simple_event_task = asyncio.create_task(self.consume_simple_event())
        self.shared_event_task = asyncio.create_task(self.consume_shared_event())

    async def shutdown(self):
        if hasattr(self.simple_event_task, "cancel"):
            self.simple_event_task.cancel()
        if hasattr(self.shared_event_task, "cancel"):
            self.shared_event_task.cancel()

import asyncio
from datetime import UTC
from datetime import datetime

import orjson
from prometheus_client import Counter
from prometheus_client import Summary
from sanic import Sanic

from common.constants import SERVER_NAME
from configs import ConfigProxy
from setup import setup_app

app = Sanic(
    name=SERVER_NAME,
    strict_slashes=False,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
    log_config={},
)

setup_app(app)

messages_counter = Counter("messages_counter", "count of messages")
speed_of_sending = Summary("speed_of_sending", "Speed of sending messages")


@app.websocket("/metrics")
async def metrics(request, ws):
    from apps.endpoint.models import Endpoint
    from apps.message.models import Message
    from apps.scheduler.models import Plan
    from apps.scheduler.models import PlanExecution

    while True:
        today_datetime = datetime.now(tz=UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # collecting metrics
        total_count_of_endpoints = await Endpoint.collection.estimated_document_count()
        total_count_of_plans = await Plan.collection.estimated_document_count()
        today_count_of_plan_executions = await PlanExecution.count_documents(
            {"created_at": {"$gte": today_datetime}}, hint=[("created_at", -1)]
        )

        start = speed_of_sending.collect()[0].samples[1].value
        with speed_of_sending.time():
            today_count_of_messages = await Message.collection.count_documents(
                {"created_at": {"$gte": today_datetime}}, hint=[("created_at", -1)]
            )
        total_count_of_messages = await Message.collection.estimated_document_count()

        # aggregate
        end = speed_of_sending.collect()[0].samples[1].value
        diff = max(
            today_count_of_messages - messages_counter.collect()[0].samples[0].value,
            0,
        )
        messages_counter.inc(diff)
        speed_of_messages = diff // (end - start)

        await asyncio.sleep(0)
        await ws.send(
            orjson.dumps(
                {
                    "total_count_of_messages": total_count_of_messages,
                    "today_count_of_messages": today_count_of_messages,
                    "speed_of_messages": speed_of_messages,
                    "total_count_of_endpoints": total_count_of_endpoints,
                    "total_count_of_plans": total_count_of_plans,
                    "today_count_of_plan_executions": today_count_of_plan_executions,
                }
            ).decode()
        )

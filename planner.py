import orjson
from apscheduler.triggers.interval import IntervalTrigger
from sanic import Sanic

from common.constants import PLANNER_NAME
from configs import ConfigProxy
from setup import setup_app

app = Sanic(
    name=PLANNER_NAME,
    strict_slashes=False,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
)
setup_app(app)


@app.before_server_start
async def add_planner_task(app):
    from apps.scheduler.task import enqueue_future_task

    app.ctx.task_scheduler.add_job(
        enqueue_future_task, trigger=IntervalTrigger(seconds=5)
    )

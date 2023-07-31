import orjson
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sanic import Sanic
from sanic.log import logger

from common.command import setup as setup_command
from common.constants import SERVER_NAME
from configs import ConfigProxy
from infrastructures.cache import CacheDependency
from infrastructures.mongodb import MongoDBDependency
from infrastructures.queue import QueueDependency
from infrastructures.websocket import WebsocketConnectionPoolDependency
from schema import setup as setup_schema

app = Sanic(
    name=SERVER_NAME,
    strict_slashes=False,
    dumps=orjson.dumps,
    loads=orjson.loads,
    config=ConfigProxy(),
)
app.ctx.dependencies = set()


@app.before_server_start
async def prepare_cache_dependency(app):
    cache_dependency = CacheDependency(app)
    await cache_dependency.prepare()
    app.ctx.dependencies.add(cache_dependency)


@app.before_server_start
async def prepare_mongodb_dependency(app):
    mongodb_dependency = MongoDBDependency(app)
    await mongodb_dependency.prepare()
    app.ctx.dependencies.add(mongodb_dependency)
    app.shared_ctx.db = mongodb_dependency._prepared


@app.before_server_start
async def prepare_queue_dependency(app):
    queue_dependency = QueueDependency(app)
    await queue_dependency.prepare()
    app.ctx.dependencies.add(queue_dependency)


@app.before_server_start
async def prepare_websocket_pool_dependency(app):
    websocket_pool_dependency = WebsocketConnectionPoolDependency(app)
    await websocket_pool_dependency.prepare()
    app.ctx.dependencies.add(websocket_pool_dependency)


@app.before_server_start
async def acquire_worker_id(app):
    # TODO: if it fails to get worker id, server won't serve any request.
    app.ctx.worker_id = await app.shared_ctx.cache.incr("worker")
    logger.info(f"Worker: {app.ctx.worker_id}")


@app.before_server_start
async def setup_graphql_schema(app):
    setup_schema(app)


@app.before_server_start
async def setup_task_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.shared_ctx.task_scheduler = scheduler

    from apps.plan.task import enqueue_future_task

    app.shared_ctx.task_scheduler.add_job(
        enqueue_future_task, trigger=IntervalTrigger(seconds=5)
    )


@app.before_server_start
async def setup_command_subscribers(app):
    async with app.shared_ctx.queue.acquire() as connection:
        await setup_command(app, connection)


@app.websocket("/websocket")
async def handle_websocket(request, ws):
    ctx = request.app.shared_ctx
    con_id = ctx.ws_pool.add_connection(ws)
    logger.info(f"new connection connected -> {con_id}")
    await ctx.ws_pool.wait_closed(con_id)

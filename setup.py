from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sanic import Sanic
from sanic.log import logger

from infrastructures.cache import CacheDependency
from infrastructures.mongodb import MongoDBDependency
from infrastructures.queue import QueueDependency
from infrastructures.websocket import WebsocketConnectionPoolDependency
from schema import setup as setup_schema


async def prepare_cache_dependency(app):
    cache_dependency = CacheDependency(app)
    await cache_dependency.prepare()
    app.ctx.dependencies.add(cache_dependency)


async def prepare_mongodb_dependency(app):
    mongodb_dependency = MongoDBDependency(app)
    await mongodb_dependency.prepare()
    app.ctx.dependencies.add(mongodb_dependency)
    app.ctx.db = mongodb_dependency._prepared


async def prepare_queue_dependency(app):
    queue_dependency = QueueDependency(app)
    await queue_dependency.prepare()
    app.ctx.dependencies.add(queue_dependency)


async def prepare_websocket_pool_dependency(app):
    websocket_pool_dependency = WebsocketConnectionPoolDependency(app)
    await websocket_pool_dependency.prepare()
    app.ctx.dependencies.add(websocket_pool_dependency)


async def acquire_worker_id(app):
    # TODO: if it fails to get worker id, server won't serve any request.
    app.ctx.workers = 4
    app.ctx.worker_id = await app.ctx.cache.incr("worker") % app.ctx.workers
    # logger.info(f"Worker: {app.ctx.worker_id}")


async def setup_graphql_schema(app):
    setup_schema(app)


async def setup_task_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.ctx.task_scheduler = scheduler
    app.ctx.task_scheduler.add_job(app.purge_tasks, trigger=IntervalTrigger(minutes=1))


async def stop_task_scheduler(app):
    app.ctx.task_scheduler.shutdown()


def setup_app(application: Sanic):
    application.ctx.dependencies = set()
    application.before_server_start(prepare_cache_dependency)
    application.before_server_start(prepare_mongodb_dependency)
    application.before_server_start(prepare_queue_dependency)
    application.before_server_start(prepare_websocket_pool_dependency)
    application.before_server_start(acquire_worker_id)
    application.before_server_start(setup_graphql_schema)
    application.before_server_start(setup_task_scheduler)
    application.before_server_stop(stop_task_scheduler)

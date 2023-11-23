from ulid import ULID
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sanic import Sanic
from sanic.log import logger
from common.constants import WORKER_CACHE_KEY, ACQUIRE_WORKER_ID_LOCK_CACHE_KEY

from infrastructures import Infrastructure


async def setup_infrastructure(app):
    infra = Infrastructure(app=app)
    infra.config.from_value(app.config)
    infra.init_resources()
    infra.check_dependencies()
    app.ctx.infra = infra


async def unset_infrastructure(app):
    if hasattr(app.ctx, "infra"):
        return
    app.ctx.infra.shutdown_resources()


async def acquire_worker_id(app):
    cache = app.ctx.infra.cache()
    async with cache.lock(ACQUIRE_WORKER_ID_LOCK_CACHE_KEY, timeout=1):
        app.ctx.workers = await cache.llen(WORKER_CACHE_KEY) + 1
        app.ctx.worker_id = str(ULID())
        app.ctx.worker_number = app.ctx.workers
        await cache.lpush(WORKER_CACHE_KEY, app.ctx.worker_id)
        logger.debug(f"acquire worker number: {app.ctx.worker_number}")


async def setup_task_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.ctx.task_scheduler = scheduler


async def stop_task_scheduler(app):
    app.ctx.task_scheduler.shutdown()


async def unregister_worker_id(app):
    cache = app.ctx.infra.cache()
    await cache.lrem(WORKER_CACHE_KEY, 0, app.ctx.worker_id)


def setup_api(app):
    from apps.endpoint.api import bp as endpoint_blueprint
    from apps.message.api import message_bp
    from apps.message.api import provider_bp
    from apps.scheduler.api import bp as scheduler_blueprint

    app.blueprint(endpoint_blueprint)
    app.blueprint(provider_bp)
    app.blueprint(message_bp)
    app.blueprint(scheduler_blueprint)


def setup_app(application: Sanic):
    application.ctx.dependencies = set()

    application.before_server_start(setup_infrastructure)
    application.before_server_start(acquire_worker_id)
    application.before_server_start(setup_task_scheduler)
    application.before_server_start(setup_api)
    application.before_server_stop(stop_task_scheduler)
    application.before_server_stop(unset_infrastructure)
    application.before_server_stop(unregister_worker_id)

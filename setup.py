from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sanic import Sanic
from sanic.log import logger

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
    # TODO: if it fails to get worker id, server won't serve any request.
    app.ctx.workers = 4
    cache = app.ctx.infra.cache()
    app.ctx.worker_id = await cache.incr("worker") % app.ctx.workers
    logger.info(f"acquire worker id: {app.ctx.worker_id}")


async def setup_task_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.ctx.task_scheduler = scheduler
    app.ctx.task_scheduler.add_job(app.purge_tasks, trigger=IntervalTrigger(minutes=1))


async def stop_task_scheduler(app):
    app.ctx.task_scheduler.shutdown()


def setup_api(app):
    from apps.endpoint.api import bp as endpoint_blueprint
    from apps.message.api import provider_bp, message_bp
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

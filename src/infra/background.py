# Standard Library
import gc

# Third Party Library
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus

# Local Folder
from .abc import Infrastructure


class BackgroundSchedulerInfrastructure(Infrastructure):
    async def health_check(self) -> HealthStatus:
        if self.background_scheduler.running:
            return HealthStatus(
                status="up",
                checks=[
                    CheckResult(check="running check", status="up", result="running")
                ],
            )
        else:
            return HealthStatus(
                status="down",
                checks=[
                    CheckResult(
                        check="running check", status="down", result="not running"
                    )
                ],
            )

    async def init(self, dsn):
        try:
            self.background_scheduler = AsyncIOScheduler()
            self.background_scheduler.add_job(
                gc.collect, trigger=IntervalTrigger(minutes=15)
            )
            self.background_scheduler.start()
        except Exception as e:
            print(e)
            pass
        return self

    async def shutdown(self, resource: Infrastructure):
        background_scheduler = getattr(self, "background_scheduler", None)
        if background_scheduler and background_scheduler.running:
            background_scheduler.shutdown(wait=True)

    def add_task(self, coroutine, trigger=None, **kwargs):
        return self.background_scheduler.add_job(coroutine, trigger=trigger, **kwargs)

    def stop_task(self, task_id):
        return self.background_scheduler.remove_job(task_id)

    def scheduled_task(self, *args, **kwargs):
        return self.background_scheduler.scheduled_job(*args, **kwargs)

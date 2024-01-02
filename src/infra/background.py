# Third Party Library
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# First Library
from infra.abc import CheckResult
from infra.abc import HealthStatus

# Local Folder
from .abc import Infrastructure


class BackgroundSchedulerInfrastructure(Infrastructure):
    # asyncio scheduler of apscheduler
    ascheduler: AsyncIOScheduler
    # asyncio scheduler of apscheduler but with ProcessPoolExecutor
    pscheduler: AsyncIOScheduler

    async def init(self):
        try:
            # init asyncio apscheduler
            self.ascheduler = AsyncIOScheduler(executor=AsyncIOExecutor())
            self.ascheduler.start()
            # init aiomultiprocess pool
            self.pscheduler = AsyncIOScheduler(executor=ProcessPoolExecutor())
            self.pscheduler.start()
        except Exception:
            self.ascheduler = None
            self.pscheduler = None
        return self

    async def shutdown(self, resource: Infrastructure):
        ascheduler = getattr(self, "ascheduler", None)
        pscheduler = getattr(self, "pscheduler", None)

        if ascheduler and ascheduler.running:
            ascheduler.shutdown(wait=True)

        if pscheduler and pscheduler.running:
            pscheduler.shutdown(wait=True)

    async def health_check(self) -> HealthStatus:
        check_results = []
        if self.ascheduler and self.ascheduler.running:
            check_results.append(
                CheckResult(
                    check="ascheduler running check",
                    status="up",
                    result="running",
                )
            )
        else:
            check_results.append(
                CheckResult(
                    check="ascheduler running check",
                    status="down",
                    result="not running",
                )
            )

        if self.pscheduler and self.pscheduler.running:
            check_results.append(
                CheckResult(
                    check="pscheduler running check",
                    status="up",
                    result="running",
                )
            )
        else:
            check_results.append(
                CheckResult(
                    check="pscheduler running check",
                    status="down",
                    result="not running",
                )
            )

        if all(map(lambda c: c.status == "up", check_results)):
            return HealthStatus(status="up", checks=check_results)
        return HealthStatus(status="down", checks=check_results)

    def _run_task_in_executor(
        self, scheduler, async_task, *, trigger=None, args=None, kwargs=None
    ) -> Job:
        if scheduler.running:
            return scheduler.add_job(
                async_task,
                trigger=trigger,
                args=args,
                kwargs=kwargs,
            )
        return None

    def run_task_in_async_executor(
        self, async_task, *, trigger=None, args=None, kwargs=None
    ) -> Job:
        """
        run async task in asyncio event loop
        """
        return self._run_task_in_executor(
            self.ascheduler,
            async_task,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
        )

    def run_task_in_process_executor(
        self, async_task, *, trigger=None, args=None, kwargs=None
    ) -> Job:
        """
        run async task in process pool
        """
        return self._run_task_in_executor(
            self.pscheduler,
            async_task,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
        )

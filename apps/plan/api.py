from typing import AsyncIterable
from typing import List
from typing import Optional

import strawberry
from strawberry.types import Info

from apps.plan.common.constants import PlanExecutionStatus
from apps.plan.common.constants import PlanTriggerType
from apps.plan.models import Plan
from apps.plan.models import PlanExecution
from apps.plan.schemas.input import CreatePlanInput
from apps.plan.schemas.input import DestroyPlanInput
from apps.plan.schemas.node import PlanExecutionNode
from apps.plan.schemas.node import PlanNode
from apps.plan.validators.plan import PlanOutputModel
from infrastructures.graphql import MessageConnection
from infrastructures.graphql import connection


@strawberry.type
class Query:
    @connection(MessageConnection[PlanNode])
    async def plans(
        self,
        info: Info,
        trigger_type_in: Optional[List[strawberry.enum(PlanTriggerType)]] = None,
        is_enabled: Optional[bool] = None,
    ) -> AsyncIterable[Plan]:
        conditions = {}
        if trigger_type_in is not None:
            conditions["triggers.type"] = {"$in": [t.value for t in trigger_type_in]}
        if is_enabled is not None:
            conditions["is_enabled"] = is_enabled
        return Plan.find(conditions)

    @connection(MessageConnection[PlanExecutionNode])
    async def plan_executions(
        self,
        info: Info,
        status_in: Optional[List[strawberry.enum(PlanExecutionStatus)]] = None,
    ) -> AsyncIterable[PlanExecution]:
        conditions = {}
        if status_in is not None:
            conditions["status"] = {"$in": [s.value for s in status_in]}
        return PlanExecution.find(conditions)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_plan(self, input: CreatePlanInput) -> PlanNode:
        model = await input.to_pydantic()
        plan = await model.save()
        return PlanOutputModel.model_validate(plan)

    @strawberry.mutation
    async def destroy_plans(self, input: DestroyPlanInput) -> int:
        model = input.to_pydantic()
        return await model.delete()

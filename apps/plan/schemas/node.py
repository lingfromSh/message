from typing import List

import strawberry
from strawberry.relay import Node
from strawberry.relay import NodeID
from umongo.fields import Reference

from apps.message.schemas.node import ProviderNode
from apps.message.schemas.node import ref_provider
from apps.plan.common.constants import PlanExecutionStatus
from apps.plan.common.constants import PlanTriggerType
from apps.plan.validators.execution import PlanExecutionOutputModel
from apps.plan.validators.plan import PlanOutputModel
from apps.plan.validators.plan import PlanSubPlanOutputModel
from apps.plan.validators.plan import PlanTriggerOutputModel
from infrastructures.graphql import ObjectID


@strawberry.experimental.pydantic.type(
    model=PlanTriggerOutputModel,
    fields=["timer_at", "repeat_at", "repeat_time", "start_time", "end_time"],
)
class PlanTriggerOutputModelType:
    type: strawberry.enum(PlanTriggerType)


@strawberry.experimental.pydantic.type(model=PlanSubPlanOutputModel)
class PlanSubPlanOutputModelType:
    provider: ProviderNode = strawberry.field(resolver=ref_provider)
    message: strawberry.scalars.JSON


@strawberry.experimental.pydantic.type(model=PlanOutputModel, use_pydantic_alias=False)
class PlanNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    name: strawberry.auto
    triggers: List[PlanTriggerOutputModelType]
    sub_plans: List[PlanSubPlanOutputModelType]

    is_enabled: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


async def ref_plan(root: "PlanExecutionNode"):
    if isinstance(root.plan, Reference):
        plan = await root.plan.fetch()
        return PlanOutputModel.model_validate(plan)


@strawberry.experimental.pydantic.type(
    model=PlanExecutionOutputModel, use_pydantic_alias=False
)
class PlanExecutionNode(Node):
    global_id: NodeID[ObjectID]
    oid: ObjectID

    plan: PlanNode = strawberry.field(resolver=ref_plan)
    status: strawberry.enum(PlanExecutionStatus)

    time_to_execute: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto

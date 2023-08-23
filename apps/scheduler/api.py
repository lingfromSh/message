import math
from sanic import Blueprint
from common.webargs import webargs
from bson.objectid import ObjectId

from apps.scheduler.validators.plan import PlanOutputModel
from apps.scheduler.validators.plan import QueryPlanInputModel
from apps.scheduler.validators.plan import CreatePlanInputModel
from apps.scheduler.validators.plan import UpdatePlanInputModel
from apps.scheduler.validators.execution import QueryPlanExecutionInputModel
from apps.scheduler.validators.execution import PlanExecutionOutputModel

from apps.scheduler.models import Plan, PlanExecution

from common.response import MessageJSONResponse


bp = Blueprint("scheduler")


@bp.get("/plans")
@webargs(query=QueryPlanInputModel)
async def filter_plans(request, **kwargs):
    filtered = []
    condition = {}

    query = kwargs["query"]
    if ids := query.get("ids"):
        condition.update({"_id": {"$in": ids}})

    if names := query.get("names"):
        condition.update({"name": {"$in": names}})

    if is_enabled := query.get("is_enabled"):
        condition.update({"is_enabled": is_enabled})

    page = query.get("page")
    page_size = query.get("page_size")
    total_item_count = await Plan.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for plan in Plan.find(condition).skip(offset).limit(limit):
        filtered.append(PlanOutputModel.model_validate(plan).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter plans successfully",
    )


@bp.post("/plans")
@webargs(body=CreatePlanInputModel)
async def create_plan(request, **kwargs):
    payload = kwargs["payload"]
    plan = Plan(**payload)
    await plan.commit()
    return MessageJSONResponse(data=PlanOutputModel.model_validate(plan).model_dump())


@bp.get("/plan/<pk:str>")
async def get_plan(request, pk):
    plan = await Plan.find_one({"_id": ObjectId(pk)})
    if not plan:
        raise ValueError("plan not found")
    return MessageJSONResponse(data=PlanOutputModel.model_validate(plan).model_dump())


@bp.patch("/plan/<pk:str>")
@webargs(body=UpdatePlanInputModel)
async def update_plan(request, pk, **kwargs):
    app = request.app
    payload = kwargs["payload"]
    plan = await Plan.find_one({"_id": ObjectId(pk)})
    if not plan:
        raise ValueError("plan not found")

    async def modify():
        if name := payload.get("name"):
            plan.name = name
        if triggers := payload.get("triggers"):
            plan.triggers = triggers
        if sub_plans := payload.get("sub_plans"):
            plan.sub_plans = sub_plans
        if payload.get("is_enabled") is not None:
            plan.is_enabled = payload["is_enabled"]
        await Plan.collection.update_one(
            {"_id": ObjectId(pk)}, plan.to_mongo(update=True), session=session
        )
        return plan

    async with await app.ctx.db_client.start_session() as session:
        plan = await session.with_transaction(modify)

    return MessageJSONResponse(data=PlanOutputModel.model_validate(plan).model_dump())


@bp.delete("/plan/<pk:str>")
async def destroy_plan(request, pk):
    result = await Plan.collection.delete_many({"_id": ObjectId(pk)})
    return MessageJSONResponse(data=result.deleted_count)


@bp.get("/executions")
@webargs(query=QueryPlanExecutionInputModel)
async def filter_executions(request, **kwargs):
    filtered = []
    condition = {}

    query = kwargs["query"]
    if ids := query.get("ids"):
        condition.update({"_id": {"$in": ids}})

    if plans := query.get("plans"):
        condition.update({"plan": {"$in": plans}})

    page = query.get("page")
    page_size = query.get("page_size")
    total_item_count = await PlanExecution.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for execution in PlanExecution.find(condition).skip(offset).limit(limit):
        filtered.append(PlanExecutionOutputModel.model_validate(execution).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter plans successfully",
    )

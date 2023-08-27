import math
from bson.objectid import ObjectId
from sanic import Blueprint
from common.webargs import webargs
from apps.template.validators.template import (
    QueryTemplateInputModel,
    CreateTemplateInputModel,
    UpdateTemplateInputModel,
    TemplateOutputModel,
)
from apps.template.models import Template
from common.response import MessageJSONResponse


bp = Blueprint("template")


@bp.get("/templates")
@webargs(query=QueryTemplateInputModel)
async def get_templates(request, **kwargs):
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
    total_item_count = await Template.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for template in Template.find(condition).skip(offset).limit(limit):
        filtered.append(TemplateOutputModel.model_validate(template).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter templates successfully",
    )


@bp.post("/templates")
@webargs(body=CreateTemplateInputModel)
async def create_template(request, **kwargs):
    payload = kwargs["payload"]
    template = Template(**payload)
    await template.commit()

    return MessageJSONResponse(
        data=TemplateOutputModel.model_validate(template).model_dump()
    )


@bp.patch("/template/<pk:str>")
@webargs(body=UpdateTemplateInputModel)
async def update_template(request, pk, **kwargs):
    template = await Template.find({"_id": ObjectId(pk)})
    if not template:
        raise ValueError("template not found")
    payload = kwargs["payload"]

    template = Template(**payload)
    await template.commit()

    return MessageJSONResponse(
        data=TemplateOutputModel.model_validate(template).model_dump()
    )


@bp.delete("/template/<pk:str>")
async def destroy_template(request, pk):
    result = await Template.collection.delete_many({"_id": ObjectId(pk)})
    return MessageJSONResponse(
        data=result.deleted_count, message="destroy template successfully"
    )


@bp.get("/template/<pk:str>")
async def get_template(request, pk):
    template = await Template.find({"_id": ObjectId(pk)})
    if not template:
        raise ValueError("template not found")
    return MessageJSONResponse(
        data=TemplateOutputModel.model_validate(template).model_dump()
    )

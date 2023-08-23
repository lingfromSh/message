import math

from sanic import Blueprint
from sanic import json

from apps.endpoint.models import Endpoint
from apps.endpoint.validators.endpoint import CreateEndpointInputModel
from apps.endpoint.validators.endpoint import EndpointOutputModel
from apps.endpoint.validators.endpoint import QueryEndpointInputModel
from apps.endpoint.validators.endpoint import UpdateEndpointInputModel
from common.response import MessageJSONResponse
from common.webargs import webargs

bp = Blueprint("endpoint")


@bp.post("/endpoints")
@webargs(body=CreateEndpointInputModel)
async def create_endpoint(request, **kwargs):
    endpoint = Endpoint(**kwargs["payload"])
    await endpoint.commit()
    return json(EndpointOutputModel.model_validate(endpoint).model_dump())


@bp.get("/endpoint/<exid:str>")
async def get_endpoint(request, exid, **kwargs):
    endpoint = await Endpoint.find_one({"external_id": exid})
    if endpoint is None:
        raise ValueError("endpoint not found")
    return MessageJSONResponse(
        data=EndpointOutputModel.model_validate(endpoint).model_dump()
    )


@bp.patch("/endpoint/<exid:str>")
@webargs(body=UpdateEndpointInputModel)
async def update_endpoint(request, exid, **kwargs):
    app = request.app

    async def modify(session):
        endpoint = await Endpoint.find_one({"external_id": exid})
        if not endpoint:
            raise ValueError("endpoint not found")
        payload = kwargs["payload"]
        if external_id := payload.get("external_id"):
            endpoint.external_id = external_id
        if tags := payload.get("tags"):
            endpoint.tags = tags
        if websockets := payload.get("websockets"):
            endpoint.websockets = websockets
        if emails := payload.get("emails"):
            endpoint.emails = emails
        await Endpoint.collection.update_one(
            {"_id": endpoint.pk}, endpoint.to_mongo(update=True), session=session
        )
        return endpoint

    async with await app.ctx.db_client.start_session() as session:
        endpoint = await session.with_transaction(modify)

    return MessageJSONResponse(
        data=EndpointOutputModel.model_validate(endpoint).model_dump()
    )


@bp.delete("/endpoint/<exid:str>")
async def destroy_endpoint(request, exid, **kwargs):
    endpoint = await Endpoint.find_one({"external_id": exid})
    if endpoint is None:
        raise ValueError("endpoint not found")
    result = await Endpoint.collection.delete_many({"external_id": exid})
    return MessageJSONResponse(data=result.deleted_count)


@bp.get("/endpoints")
@webargs(query=QueryEndpointInputModel)
async def filter_endpoints(request, **kwargs):
    filtered = []
    condition = {}

    query = kwargs["query"]
    if external_ids := query.get("external_ids"):
        condition.update({"external_id": {"$in": external_ids}})

    if tags := query.get("tags"):
        condition.update({"tags": {"$in": tags}})

    if websockets := query.get("websockets"):
        condition.update({"websockets": {"$in": websockets}})

    if tags := query.get("tags"):
        condition.update({"tags": {"$in": tags}})

    page = query.get("page")
    page_size = query.get("page_size")
    total_item_count = await Endpoint.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for endpoint in Endpoint.find(condition).skip(offset).limit(limit):
        filtered.append(EndpointOutputModel.model_validate(endpoint).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter endpoint successfully",
    )

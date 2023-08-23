import math
from bson.objectid import ObjectId
from sanic import Blueprint

from common.webargs import webargs
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.validators.message import MessageOutputModel
from apps.message.validators.message import QueryMessageInputModel
from apps.message.validators.message import SendMessageInputModel
from apps.message.validators.provider import ProviderOutputModel
from apps.message.validators.provider import CreateProviderInputModel
from apps.message.validators.provider import UpdateProviderInputModel
from apps.message.validators.provider import QueryProviderInputModel
from common.webargs import webargs
from common.response import MessageJSONResponse

provider_bp = Blueprint("provider")
message_bp = Blueprint("message")


@provider_bp.get("/providers")
@webargs(query=QueryProviderInputModel)
async def filter_providers(request, **kwargs):
    filtered = []
    condition = {}

    query = kwargs["query"]
    if codes := query.get("codes"):
        condition.update({"code": {"$in": codes}})

    if types := query.get("types"):
        condition.update({"types": {"$in": types}})

    if names := query.get("names"):
        condition.update({"names": {"$in": names}})

    if ids := query.get("ids"):
        condition.update({"ids": {"$in": [ObjectId(id) for id in ids]}})

    page = query.get("page")
    page_size = query.get("page_size")
    total_item_count = await Provider.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for provider in Provider.find(condition).skip(offset).limit(limit):
        filtered.append(ProviderOutputModel.model_validate(provider).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter providers successfully",
    )


@provider_bp.post("/providers")
@webargs(body=CreateProviderInputModel)
async def create_provider(request, **kwargs):
    payload = kwargs["payload"]
    provider = Provider(**payload)
    await provider.commit()
    return MessageJSONResponse(
        data=ProviderOutputModel.model_validate(provider).model_dump()
    )


@provider_bp.get("/provider/<pk:str>")
async def get_provider(request, pk, **kwargs):
    provider = await Provider.find_one({"_id": ObjectId(pk)})
    if not provider:
        raise ValueError("provider not found")
    return MessageJSONResponse(
        data=ProviderOutputModel.model_validate(provider).model_dump()
    )


@provider_bp.patch("/provider/<pk:str>")
@webargs(body=UpdateProviderInputModel)
async def update_provider(request, pk, **kwargs):
    app = request.app
    payload = kwargs["payload"]

    async def modify(session):
        provider = await Provider.find_one({"_id": ObjectId(pk)})
        if type := payload.get("type"):
            provider.type = type
        if code := payload.get("code"):
            provider.code = code
        if name := payload.get("name"):
            provider.name = name
        if config := payload.get("config"):
            provider.config = config

        provider.updated_at = payload["updated_at"]
        await Provider.collection.update_one(
            {"_id": ObjectId(pk)}, provider.to_mongo(update=True), session=session
        )
        return provider

    async with await app.ctx.db_client.start_session() as session:
        provider = await session.with_transaction(modify)
    return MessageJSONResponse(
        data=ProviderOutputModel.model_validate(provider).model_dump()
    )


@provider_bp.delete("/provider/<pk:str>")
async def destroy_provider(request, pk, **kwargs):
    result = await Provider.collection.delete_many({"_id": ObjectId(pk)})
    return MessageJSONResponse(data=result.deleted_count)


@message_bp.get("/messages")
@webargs(query=QueryMessageInputModel)
async def filter_messages(request, **kwargs):
    filtered = []
    condition = {}

    query = kwargs["query"]
    if providers := query.get("providers"):
        condition.update({"provider": {"$in": providers}})

    if status_in := query.get("status_in"):
        condition.update({"status": {"$in": status_in}})

    if ids := query.get("ids"):
        condition.update({"ids": {"$in": ids}})

    page = query.get("page")
    page_size = query.get("page_size")
    total_item_count = await Message.count_documents(condition)
    total_page_count = math.ceil(total_item_count / page_size)

    limit = page_size
    offset = (page - 1) * page_size
    async for message in Message.find(condition).skip(offset).limit(limit):
        filtered.append(MessageOutputModel.model_validate(message).model_dump())

    return MessageJSONResponse(
        data={
            "page": page,
            "page_size": page_size,
            "total_item_count": total_item_count,
            "total_page_count": total_page_count,
            "results": filtered,
        },
        message="filter messages successfully",
    )


@message_bp.get("/message/<pk:str>")
async def get_message(request, pk, **kwargs):
    message = await Message.find_one({"_id": ObjectId(pk)})
    if not message:
        raise ValueError("message not found")
    return MessageJSONResponse(
        data=MessageOutputModel.model_validate(message).model_dump()
    )


@message_bp.post("/messages")
@webargs(body=SendMessageInputModel)
async def send_message(request, **kwargs):
    payload = kwargs["payload"]

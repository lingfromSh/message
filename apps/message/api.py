import math

from aio_pika.message import Message as QueueMessage
from bson.objectid import ObjectId
from sanic import Blueprint

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.subscriber import ImmediateBroadcastMessageTopicSubscriber
from apps.message.utils import get_provider as get_provider_cls
from apps.message.validators.message import MessageOutputModel
from apps.message.validators.message import QueryMessageInputModel
from apps.message.validators.message import SendMessageInputModel
from apps.message.validators.provider import CreateProviderInputModel
from apps.message.validators.provider import ProviderOutputModel
from apps.message.validators.provider import QueryProviderInputModel
from apps.message.validators.provider import UpdateProviderInputModel
from apps.template.utils import get_db_template
from common.response import MessageJSONResponse
from common.webargs import webargs

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

    async with await app.ctx.infra.database().client.start_session() as session:
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
    need_query_providers = set()
    async for message in Message.find(condition).sort({"created_at": -1}).skip(
        offset
    ).limit(limit):
        dump_messgage = MessageOutputModel.model_validate(message).model_dump()
        need_query_providers.add(dump_messgage["provider"])
        filtered.append(dump_messgage)

    providers = {
        provider.pk: ProviderOutputModel.model_validate(provider).model_dump()
        async for provider in Provider.find(
            {"_id": {"$in": list(need_query_providers)}}
        )
    }

    for item in filtered:
        item["provider"] = providers.get(item.pop("provider"))

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

    db_provider = await Provider.find_one({"_id": ObjectId(payload["provider"])})
    if not db_provider:
        raise ValueError("provider not found")

    # check whether this provider is valid
    provider_cls = get_provider_cls(db_provider.type, db_provider.code)

    # check if message is valid
    realm = payload["realm"]
    if not isinstance(realm, dict):
        template = await get_db_template(realm)
        if not template.is_enabled:
            raise ValueError("failed to send message because the template is disabled")
        payload["realm"] = template.content

    validated = provider_cls.validate_message(payload["realm"])

    db_message = Message(
        provider=db_provider.pk,
        realm=payload["realm"],
        status=MessageStatus.SENDING.value,
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
    )

    if provider_cls.info.type == MessageProviderType.WEBSOCKET:
        await db_message.commit()
        immediate_message = (
            ImmediateBroadcastMessageTopicSubscriber.message_model.model_validate(
                {
                    "provider": {
                        "id": db_provider.pk,
                        "type": db_provider.type,
                        "code": db_provider.code,
                        "config": db_provider.config,
                    },
                    "message": {"id": db_message.pk, "realm": db_message.realm},
                }
            )
        )
        await ImmediateBroadcastMessageTopicSubscriber.notify(
            message=QueueMessage(body=immediate_message.model_dump_json().encode()),
        )
    else:
        result = await provider_cls(**(db_provider.config or {})).send(
            db_provider.id, validated
        )
        db_message.status = result.status.value
        await db_message.commit()

    message_dict = MessageOutputModel.model_validate(db_message).model_dump()
    message_dict["provider"] = ProviderOutputModel.model_validate(
        db_provider
    ).model_dump()
    return MessageJSONResponse(
        data=message_dict,
        message="send message successfully",
    )

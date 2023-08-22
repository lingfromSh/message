from typing import AsyncIterable
from datetime import datetime, UTC
from typing import List
from typing import Optional
from bson.objectid import ObjectId

import strawberry
from strawberry.types import Info

from aio_pika.message import Message as QueueMessage
from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.models import Message
from apps.message.models import Provider
from apps.message.schemas.input import CreateProviderInput
from apps.message.schemas.input import DestroyProviderInput
from apps.message.schemas.input import SendMessageInput
from apps.message.schemas.input import UpdateProviderInput
from apps.message.schemas.node import MessageNode
from apps.message.schemas.node import ProviderNode
from apps.message.validators.provider import ProviderOutputModel
from apps.message.validators.task import ImmediateTask
from apps.message.subscriber import ImmediateMessageTopicSubscriber
from apps.message.utils import get_provider
from infrastructures.graphql import MessageConnection
from infrastructures.graphql import connection


@strawberry.type
class Query:
    @connection(MessageConnection[ProviderNode])
    async def providers(
        self,
        info: Info,
        type_in: Optional[List[strawberry.enum(MessageProviderType)]] = None,
        code_in: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> AsyncIterable[Provider]:
        conditions = {}
        if type_in is not None:
            conditions["type"] = {"$in": [t.value for t in type_in]}
        if code_in is not None:
            conditions["code"] = {"$in": code_in}
        if name is not None:
            conditions["name"] = name
        return Provider.find(conditions)

    @connection(MessageConnection[MessageNode])
    async def messages(
        self,
        info: Info,
        status_in: Optional[List[strawberry.enum(MessageStatus)]] = None,
    ) -> AsyncIterable[Message]:
        conditions = {}
        if status_in is not None:
            conditions["status"] = {"$in": status_in}
        return Message.find(conditions)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_provider(self, input: CreateProviderInput) -> ProviderNode:
        model = input.to_pydantic()
        provider = await model.save()
        return ProviderOutputModel.model_validate(provider)

    @strawberry.mutation
    async def update_provider(self, input: UpdateProviderInput) -> ProviderNode:
        model = input.to_pydantic()
        provider = await model.save()
        return ProviderOutputModel.model_validate(provider)

    @strawberry.mutation
    async def destroy_providers(self, input: DestroyProviderInput) -> int:
        model = input.to_pydantic()
        return await model.delete()

    @strawberry.mutation
    async def send_message(self, info: Info, input: SendMessageInput) -> MessageNode:
        app = info.context.get("request").app
        dbprovider = await Provider.find_one({"_id": input.provider})
        if not dbprovider:
            raise ValueError("provider not found")

        config = dbprovider.config or {}
        provider = get_provider(dbprovider.type, dbprovider.code)(**config)
        validated = provider.validate_message(input.realm)
        message_data = dict(
            provider=dbprovider,
            realm=input.realm,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        if dbprovider.type != MessageProviderType.WEBSOCKET.value:
            sent = await provider.send(input.provider, message=validated)
            message_data["status"] = (
                MessageStatus.SUCCEEDED.value if sent else MessageStatus.FAILED.value
            )
        else:
            message_data["status"] = MessageStatus.SENDING.value

        message = Message(**message_data)
        message.id = ObjectId()

        if dbprovider.type == MessageProviderType.WEBSOCKET.value:
            task = ImmediateTask(
                provider={
                    "oid": dbprovider.pk,
                    "type": dbprovider.type,
                    "code": dbprovider.code,
                    "config": config,
                },
                message={
                    "oid": message.pk,
                    "realm": message.realm,
                },
            )

            app.add_task(
                ImmediateMessageTopicSubscriber.notify(
                    None, message=QueueMessage(body=task.model_dump_json().encode())
                )
            )
            app.add_task(message.commit())
        return MessageNode(
            global_id=message.pk,
            oid=message.pk,
            realm=message.realm,
            status=message.status,
            provider=ProviderNode(
                global_id=dbprovider.pk,
                oid=dbprovider.pk,
                name=dbprovider.name,
                type=dbprovider.type,
                code=dbprovider.code,
                config=dbprovider.config,
                created_at=dbprovider.created_at,
                updated_at=dbprovider.updated_at,
            ),
            created_at=message.created_at,
            updated_at=message.updated_at,
        )

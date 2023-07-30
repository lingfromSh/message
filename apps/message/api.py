import inspect
from typing import AsyncIterable
from typing import List
from typing import Optional

import strawberry
from strawberry.types import Info

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
from apps.message.validators.message import MessageOutputModel
from apps.message.validators.provider import ProviderOutputModel
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
    async def send_message(self, input: SendMessageInput) -> MessageNode:
        model = await input.to_pydantic()
        message = await model.send()
        output = MessageOutputModel.model_validate(message)
        return output

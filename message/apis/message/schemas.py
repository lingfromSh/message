# Standard Library
import asyncio
import time
import typing

# Third Party Library
import orjson
import strawberry
from message import applications
from message import exceptions
from message.common.constants import MessageStatusEnum
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from strawberry import relay

# Local Folder
from .objecttypes import MessageTortoiseORMNode


@strawberry.type(description="Message API")
class Query:
    @connection(TortoiseORMPaginationConnection[MessageTortoiseORMNode])
    async def messages(
        self,
        provider: typing.Optional[typing.List[relay.GlobalID]] = None,
        users: typing.Optional[typing.List[relay.GlobalID]] = None,
        endpoints: typing.Optional[typing.List[relay.GlobalID]] = None,
        statuses: typing.Optional[
            typing.List[strawberry.enum(MessageStatusEnum)]
        ] = None,
    ) -> typing.AsyncIterable[MessageTortoiseORMNode]:
        application = applications.MessageApplication()
        conditions = {}
        if provider is not None:
            conditions["provider_id__in"] = [provider.node_id for provider in provider]
        if users is not None:
            conditions["end_users__id__in"] = [user.node_id for user in users]
        if endpoints is not None:
            conditions["endpoints__id__in"] = [
                endpoint.node_id for endpoint in endpoints
            ]
        if statuses is not None:
            conditions["status__in"] = [status.value for status in statuses]
        return await (await application.get_messages(conditions))


@strawberry.type(description="Message API")
class Mutation:
    @strawberry.mutation(description="Send a new message to users")
    async def message_send(
        self,
        provider: relay.GlobalID,
        content: strawberry.scalars.JSON,
        users: typing.Optional[typing.List[relay.GlobalID]] = None,
        endpoints: typing.Optional[typing.List[relay.GlobalID]] = None,
        contacts: typing.Optional[typing.List[strawberry.scalars.JSON]] = None,
    ) -> str:
        message_application = applications.MessageApplication()
        message_id = await message_application.send_message(
            provider_id=provider.node_id,
            content=orjson.dumps(content).decode(),
            users=[user.node_id for user in users] if users else [],
            endpoints=[endpoint.node_id for endpoint in endpoints] if endpoints else [],
            contacts=contacts,
        )
        return relay.GlobalID(
            type_name=MessageTortoiseORMNode.__name__,
            node_id=message_id,
        )


@strawberry.type(description="Message API")
class Subscription:
    @strawberry.subscription(description="Watch a message")
    async def message(
        self, id: relay.GlobalID, interval: typing.Optional[int] = 1
    ) -> typing.AsyncGenerator[typing.Optional[MessageTortoiseORMNode], None]:
        interval = max(interval, 1)
        message = None
        application = applications.MessageApplication()

        while message is None:
            try:
                message = await application.get_message(id.node_id)
            except exceptions.MessageNotFoundError:
                message = None
                yield message
                await asyncio.sleep(interval)

        while message is not None:
            yield await MessageTortoiseORMNode.resolve_orm(message)
            await asyncio.sleep(interval)

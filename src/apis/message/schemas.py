# Standard Library
import asyncio
import typing

# Third Party Library
import orjson
import strawberry
from strawberry import relay

# First Library
import applications
import exceptions
from common.constants import MessageStatusEnum
from common.graphql.relay import TortoiseORMPaginationConnection
from common.graphql.relay import connection

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
        return await application.get_messages(conditions)


@strawberry.type(description="Message API")
class Mutation:
    @strawberry.mutation(description="Send a new message to users")
    async def message_send(
        self,
        provider: relay.GlobalID,
        message: strawberry.scalars.JSON,
        users: typing.Optional[typing.List[relay.GlobalID]] = None,
        endpoints: typing.Optional[typing.List[relay.GlobalID]] = None,
        contacts: typing.Optional[typing.List[strawberry.scalars.JSON]] = None,
    ) -> str:
        if all([users is None, endpoints is None, contacts is None]):
            raise exceptions.MessageSendRequiredReceiversError
        endpoint_application = applications.EndpointApplication()
        message_application = applications.MessageApplication()
        user_application = applications.UserApplication()
        provider_application = applications.ProviderApplication()
        provider_domain = await provider_application.get_provider(id=provider.node_id)
        if users is not None:
            user_domains = await (
                await user_application.get_users(
                    conditions={"id__in": [user.node_id for user in users]}
                )
            )
        else:
            user_domains = []
        if endpoints is not None:
            endpoint_domains = await (
                await endpoint_application.get_endpoints(
                    conditions={"id__in": [endpoint.node_id for endpoint in endpoints]}
                )
            )
        else:
            endpoint_domains = []
        message_id = await message_application.create_message(
            provider_domain,
            message=orjson.dumps(message).decode(),
            users=user_domains,
            endpoints=endpoint_domains,
            contacts=contacts or [],
            background=True,
        )
        return relay.GlobalID(
            type_name=MessageTortoiseORMNode.__name__,
            node_id=str(message_id),
        )


@strawberry.type(description="Message API")
class Subscription:
    @strawberry.subscription(description="Watch a message")
    async def message(
        self, id: relay.GlobalID, interval: typing.Optional[int] = 1
    ) -> typing.AsyncGenerator[MessageTortoiseORMNode, None]:
        interval = max(interval, 1)
        while True:
            application = applications.MessageApplication()
            message = await application.get_message(id.node_id)
            if message is None:
                raise exceptions.MessageNotFoundError
            yield await MessageTortoiseORMNode.resolve_orm(message)
            await asyncio.sleep(interval)

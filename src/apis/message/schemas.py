# Standard Library
import typing

# Third Party Library
import strawberry
from strawberry import relay

# First Library
from common.graphql.relay import TortoiseORMPaginationConnection
from common.graphql.relay import connection


@strawberry.type(description="Message API")
class Query:
    ...


@strawberry.type(description="Message API")
class Mutation:
    @strawberry.mutation(description="Send a new message to users")
    async def message_send(
        self,
        provider: relay.GlobalID,
        message: strawberry.scalars.JSON,
        users: typing.List[relay.GlobalID] = None,
        endpoints: typing.List[relay.GlobalID] = None,
        contacts: typing.List[strawberry.scalars.JSON] = None,
    ) -> bool:
        ...

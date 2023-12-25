# Standard Library
from dataclasses import dataclass

# Third Party Library
import strawberry
from strawberry import relay
from strawberry.schema.config import StrawberryConfig

# Local Folder
from .contact import Mutation as ContactMutation
from .contact import Query as ContactQuery
from .endpoint import Mutation as EndpointMutation
from .endpoint import Query as EndpointQuery
from .health import Query as HealthQuery
from .health import Subscription as HealthSubscription
from .message import Mutation as MessageMutation
from .message import Query as MessageQuery
from .provider import Mutation as ProviderMutation
from .provider import Query as ProviderQuery
from .user import Mutation as UserMutation
from .user import Query as UserQuery


@strawberry.type
class Query(
    ContactQuery,
    EndpointQuery,
    HealthQuery,
    MessageQuery,
    ProviderQuery,
    UserQuery,
):
    node: relay.Node = relay.node()


@strawberry.type
class Mutation(
    ContactMutation,
    EndpointMutation,
    MessageMutation,
    ProviderMutation,
    UserMutation,
):
    ...


@strawberry.type
class Subscription(HealthSubscription):
    ...


@dataclass
class SchemaConfig(StrawberryConfig):
    relay_default_page_size: int = 10


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=SchemaConfig(),
)

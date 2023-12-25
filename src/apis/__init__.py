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
from .user import Mutation as UserMutation
from .user import Query as UserQuery


@strawberry.type
class Query(ContactQuery, EndpointQuery, HealthQuery, UserQuery):
    node: relay.Node = relay.node()


@strawberry.type
class Mutation(ContactMutation, EndpointMutation, UserMutation):
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

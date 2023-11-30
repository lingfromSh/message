from strawberry.schema import Schema

from apis.endpoint import Mutation as EndpointMutation
from apis.endpoint import Query as EndpointQuery
from apis.endpoint import Subscription as EndpointSubscription


class Query(EndpointQuery):
    ...


class Mutation(EndpointMutation):
    ...


class Subscribtion(EndpointSubscription):
    ...


schema = Schema(query=Query, mutation=Mutation, subscription=Subscribtion)

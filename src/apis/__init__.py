# Third Party Library
import strawberry

# Local Folder
from .health import Query as HealthQuery
from .health import Subscription as HealthSubscription


class Query(HealthQuery):
    pass


class Subscription(HealthSubscription):
    pass


schema = strawberry.Schema(query=Query, subscription=Subscription)

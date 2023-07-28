from typing import List

import strawberry

from common.constants import HEALTHY
from common.constants import UNHEALTHY
from common.health import HealthStatus
from infrastructures.graphql import MessageGraphQLConfig
from infrastructures.graphql import MessageGraphQLView


def setup(app) -> None:
    from apps.message.api import Mutation as MessageMutation
    from apps.message.api import Query as MessageQuery

    @strawberry.type
    class Query(MessageQuery):
        node: strawberry.relay.Node = strawberry.relay.node()

        @strawberry.field
        async def health(self, info) -> List[HealthStatus]:
            """
            return health status of server
            """
            request = info.context["request"]
            ret = []
            for dependency in request.app.ctx.dependencies:
                status = HealthStatus(name=dependency.name, healthy=UNHEALTHY)
                if await dependency.check():
                    status.healthy = HEALTHY
                else:
                    status.healthy = UNHEALTHY
                ret.append(status)
            return sorted(ret, key=lambda x: x.name)

    @strawberry.type
    class Mutation(MessageMutation):
        ...

    app.add_route(
        MessageGraphQLView.as_view(
            schema=strawberry.Schema(
                query=Query,
                mutation=Mutation,
                config=MessageGraphQLConfig(
                    relay_default_page_size=app.config.API.GRAPHQL_RELAY_DEFAULT_PAGE_SIZE,
                    relay_min_page_size=app.config.API.GRAPHQL_RELAY_MIN_PAGE_SIZE,
                    relay_max_page_size=app.config.API.GRAPHQL_RELAY_MAX_PAGE_SIZE,
                ),
            ),
            graphiql=app.config.API.GRAPHIQL_ENABLED,
        ),
        "/graphql",
    )

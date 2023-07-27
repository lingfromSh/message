import strawberry
from typing import List
from common.constants import HEALTHY
from common.constants import UNHEALTHY
from common.health import HealthStatus
from infrastructures.graphql import MessageGraphQLView


def setup(app) -> None:
    from apps.message.api import Query as MessageQuery
    from apps.message.api import Mutation as MessageMutation

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
            schema=strawberry.Schema(query=Query, mutation=Mutation),
            graphiql=app.config.API.GRAPHIQL_ENABLED,
        ),
        "/graphql",
    )

import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="execution")
    async def get_execution(self, info, id: strawberry.ID) -> Execution:
        ...

    @strawberry.field(name="executions")
    async def get_executions(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Execution]:
        ...


@strawberry.subscription
class Subscription:
    ...

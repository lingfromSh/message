import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="plan")
    async def get_plan(self, info, id: strawberry.ID) -> Plan:
        ...

    @strawberry.field(name="plans")
    async def get_plans(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Plan]:
        ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_plan(self, info, input: CreatePlanInputModel):
        ...

    @strawberry.mutation
    async def modify_plan(self, info, id: strawberry.ID, input: ModifyPlanInputModel):
        ...

    @strawberry.mutation
    async def destroy_plans(self, info, input: DestroyPlanInputModel):
        ...


@strawberry.subscription
class Subscription:
    ...

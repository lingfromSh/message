import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="provider")
    async def get_provider(self, info, id: strawberry.ID) -> Provider:
        ...

    @strawberry.field(name="providers")
    async def get_providers(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Provider]:
        ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_provider(self, info, input: CreateProviderInputModel):
        ...

    @strawberry.mutation
    async def modify_provider(self, info, id: strawberry.ID, input: ModifyProviderInputModel):
        ...

    @strawberry.mutation
    async def destroy_providers(self, info, input: DestroyProviderInputModel):
        ...


@strawberry.subscription
class Subscription:
    ...

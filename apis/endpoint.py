import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="endpoint")
    async def get_endpoint(self, info, id: strawberry.ID) -> Endpoint:
        ...

    @strawberry.field(name="endpoints")
    async def get_endpoints(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Endpoint]:
        ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_endpoint(self, info, input: CreateEndpointInputModel):
        ...

    @strawberry.mutation
    async def modify_endpoint(
        self, info, id: strawberry.ID, input: ModifyEndpointInputModel
    ):
        ...

    @strawberry.mutation
    async def destroy_endpoints(self, info, input: DestroyEndpointInputModel):
        ...

    @strawberry.mutation
    async def import_endpoints(self, info, input: ImportEndpointInputModel):
        ...

    @strawberry.mutation
    async def export_endpoints(self, info, input: ExportEndpointInputModel):
        ...


@strawberry.subscription
class Subscription:
    ...

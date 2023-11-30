import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="template")
    async def get_template(self, info, id: strawberry.ID) -> Template:
        ...

    @strawberry.field(name="templates")
    async def get_templates(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Template]:
        ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_template(self, info, input: CreateTemplateInputModel):
        ...

    @strawberry.mutation
    async def modify_template(
        self, info, id: strawberry.ID, input: ModifyTemplateInputModel
    ):
        ...

    @strawberry.mutation
    async def destroy_templates(self, info, input: DestroyTemplateInputModel):
        ...


@strawberry.subscription
class Subscription:
    ...

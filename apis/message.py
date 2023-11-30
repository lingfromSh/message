import typing

import strawberry


@strawberry.type
class Query:
    @strawberry.field(name="message")
    async def get_message(self, info, id: strawberry.ID) -> Message:
        ...

    @strawberry.field(name="messages")
    async def get_messages(
        self, info, ids: typing.Optional[typing.List[strawberry.ID]] = None
    ) -> typing.List[Message]:
        ...

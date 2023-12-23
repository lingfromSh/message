# Standard Library
import typing
from datetime import datetime

# Third Party Library
import strawberry
from strawberry import relay

# First Library
import applications
from common.graphql.relay import TortoiseORMPaginationConnection

# Local Folder
from .objecttypes import ContactDefinitionStrawberryType
from .objecttypes import ContactTortoiseORMNode


@strawberry.type(description="Contact API")
class Query:
    @relay.connection(TortoiseORMPaginationConnection[ContactTortoiseORMNode])
    async def contacts(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        name: typing.Optional[typing.List[str]] = None,
        code: typing.Optional[typing.List[str]] = None,
        created_at_before: typing.Optional[datetime] = None,
        created_at_after: typing.Optional[datetime] = None,
        updated_at_before: typing.Optional[datetime] = None,
        updated_at_after: typing.Optional[datetime] = None,
    ) -> typing.AsyncIterable[ContactTortoiseORMNode]:
        application = applications.ContactApplication()
        conditions = {}
        if ids is not None:
            conditions["id__in"] = [id.node_id for id in ids]
        if name is not None:
            conditions["name__contains"] = name
        if code is not None:
            conditions["code__contains"] = code
        if created_at_before is not None:
            conditions["created_at__lt"] = created_at_before
        if created_at_after is not None:
            conditions["created_at__gt"] = created_at_after
        if updated_at_before is not None:
            conditions["updated_at__lt"] = updated_at_before
        if updated_at_after is not None:
            conditions["updated_at__gt"] = updated_at_after
        return application.get_contacts(conditions=conditions)


@strawberry.type(description="Contact API")
class Mutation:
    @strawberry.mutation(description="Register a contact")
    async def contact_register(
        self,
        name: str,
        code: str,
        definition: ContactDefinitionStrawberryType,
        description: typing.Optional[str] = None,
    ) -> ContactTortoiseORMNode:
        application = applications.ContactApplication()
        contact = await application.create_contact(
            name=name,
            code=code,
            description=description,
            definition=definition.to_pydantic(),
        )
        return ContactTortoiseORMNode.resolve_orm(contact)

    @strawberry.mutation(description="Update contact")
    async def contact_update(
        self,
        id: relay.GlobalID,
        code: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        definition: typing.Optional[ContactDefinitionStrawberryType] = None,
    ) -> ContactTortoiseORMNode:
        application = applications.ContactApplication()
        contact = await application.get_contact(id=id)
        await application.update_contact(
            contact,
            code=code,
            name=name,
            description=description,
            definition=definition.to_pydantic() if definition else None,
        )
        return ContactTortoiseORMNode.resolve_orm(contact)

    @strawberry.mutation(description="Destroy contact")
    async def contact_destroy(self, ids: typing.List[relay.GlobalID]) -> str:
        application = applications.ContactApplication()
        return await application.destroy_contacts(*(id.node_id for id in ids))
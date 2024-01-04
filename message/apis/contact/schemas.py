# Standard Library
import typing

# Third Party Library
import strawberry
from message import applications
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from strawberry import relay

# Local Folder
from .objecttypes import ContactDefinitionStrawberryType
from .objecttypes import ContactTortoiseORMNode


@strawberry.type(description="Contact API")
class Query:
    @connection(TortoiseORMPaginationConnection[ContactTortoiseORMNode])
    async def contacts(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        name: typing.Optional[str] = None,
        code: typing.Optional[str] = None,
    ) -> typing.AsyncIterable[ContactTortoiseORMNode]:
        application = applications.ContactApplication()
        conditions = {}
        if ids is not None:
            conditions["id__in"] = [id.node_id for id in ids]
        if name is not None:
            conditions["name__contains"] = name
        if code is not None:
            conditions["code__contains"] = code

        return await application.get_contacts(conditions=conditions)


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
            definition={
                "type": definition.type.value,
                "contact_schema": definition.contact_schema,
            },
        )
        return await ContactTortoiseORMNode.resolve_orm(contact)

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
        contact = await application.get_contact(id=id.node_id)
        await application.update_contact(
            contact,
            code=code,
            name=name,
            description=description,
            definition={
                "type": definition.type.value,
                "contact_schema": definition.contact_schema,
            }
            if definition
            else None,
        )
        return await ContactTortoiseORMNode.resolve_orm(contact)

    @strawberry.mutation(description="Destroy contact")
    async def contact_destroy(self, ids: typing.List[relay.GlobalID]) -> str:
        application = applications.ContactApplication()
        return await application.destroy_contacts(*(id.node_id for id in ids))

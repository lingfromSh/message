# Standard Library
import typing

# Third Party Library
import strawberry
from message import exceptions
from message.apis.contact.errors import (
    ContactDuplicateCodeError as StrawberryContactDuplicateCodeError,
)
from message.apis.contact.objecttypes import ContactDefinition
from message.apis.contact.objecttypes import ContactTortoiseORMNode
from message.common.graphql.relay import TortoiseORMPaginationConnection
from message.common.graphql.relay import connection
from message.exceptions.contact import ContactDuplicatedCodeError
from message.wiring import ApplicationContainer
from strawberry import relay


@strawberry.type(description="Contact API")
class Query:
    @connection(TortoiseORMPaginationConnection[ContactTortoiseORMNode])
    async def contacts(
        self,
        ids: typing.Optional[typing.List[relay.GlobalID]] = None,
        name: typing.Optional[str] = None,
        code: typing.Optional[str] = None,
        is_builtin: typing.Optional[bool] = None,
    ) -> typing.AsyncIterable[ContactTortoiseORMNode]:
        application = ApplicationContainer.contact_application()
        filters = {}
        if ids is not None:
            filters["id__in"] = [id.node_id for id in ids]
        if name is not None:
            filters["name__contains"] = name
        if code is not None:
            filters["code__contains"] = code
        if is_builtin is not None:
            filters["is_builtin"] = is_builtin

        return await application.get_many(filters=filters)

    @strawberry.field(
        description="validate endpoint's value whether is valid or not according to the contact's definition."
    )
    async def contact_validate(
        self,
        id: relay.GlobalID,
        regex_value: typing.Optional[str] = None,
        jsonschema_value: typing.Optional[strawberry.scalars.JSON] = None,
    ) -> bool:
        """
        Validate endpoint's value whether is valid or not according to the contact's definition.
        """
        if regex_value is None and jsonschema_value is None:
            raise exceptions.ContactValidateMissingRequiredParamsError(
                context={"params": ["regex_value", "jsonschema_value"]}
            )

        application = ApplicationContainer.contact_application()
        contact = await application.get(id=id.node_id)
        if not contact:
            raise exceptions.ContactNotFoundError

        if regex_value is not None:
            return contact.validate_endpoint_value(regex_value)
        elif jsonschema_value is not None:
            return contact.validate_endpoint_value(jsonschema_value)
        else:
            # this branch will never happen
            return False


@strawberry.type(description="Contact API")
class Mutation:
    @strawberry.mutation(description="Create a kind of contact")
    async def contact_create(
        self,
        name: str,
        code: str,
        definition: ContactDefinition,
        description: typing.Optional[str] = None,
    ) -> ContactTortoiseORMNode:
        application = ApplicationContainer.contact_application()

        try:
            contact = await application.create(
                name=name,
                code=code,
                description=description,
                definition={
                    "type": definition.type,
                    "contact_schema": definition.value,
                },
                is_builtin=False,
            )
            return await ContactTortoiseORMNode.resolve_orm(contact)
        except ValueError:
            raise exceptions.ContactValidationError

    @strawberry.mutation(description="Update contact")
    async def contact_update(
        self,
        id: relay.GlobalID,
        code: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        definition: typing.Optional[ContactDefinition] = None,
    ) -> ContactTortoiseORMNode:
        application = ApplicationContainer.contact_application()
        contact = await application.get_contact(id=id.node_id)
        if not contact:
            raise exceptions.ContactNotFoundError

        update_kwargs = {}
        if code is not None:
            update_kwargs["code"] = code
        if name is not None:
            update_kwargs["name"] = name
        if description is not None:
            update_kwargs["description"] = description
        if definition is not None:
            update_kwargs["definition"] = {
                "type": definition.type,
                "contact_schema": definition.value,
            }

        contact = await application.update(contact, **update_kwargs)
        return await ContactTortoiseORMNode.resolve_orm(contact)

    @strawberry.mutation(description="Destroy contact")
    async def contact_destroy(self, ids: typing.List[relay.GlobalID]) -> str:
        ids = [id.node_id for id in ids]
        application = ApplicationContainer.contact_application()

        qs = await application.get_many(filters={"id__in": ids, "is_builtin": True})
        if await qs.exists():
            raise exceptions.ContactCannotDeleteBuiltinError

        deleted = await application.delete_many(
            filters={"id__in": ids, "is_builtin": False}
        )
        return "ok" if deleted else "failed"

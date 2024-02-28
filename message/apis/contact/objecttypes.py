# Third Party Library
import strawberry
from message import models
from message.apis.contact.enums import ContactDefinitionTypeEnum
from message.common.graphql.relay import TortoiseORMNode


class ContactTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Contact


@strawberry.input
class ContactDefinition:
    type: strawberry.enum(ContactDefinitionTypeEnum)  # type: ignore
    value: strawberry.scalars.JSON

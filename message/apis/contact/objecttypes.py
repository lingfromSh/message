# Standard Library
from enum import Enum

# Third Party Library
import strawberry
from message import models
from message.common.graphql.relay import TortoiseORMNode


class ContactDefinitionTypeEnum(Enum):
    JSONSCHEMA = "jsonschema"


@strawberry.input
class ContactDefinitionStrawberryType:
    type: strawberry.enum(ContactDefinitionTypeEnum)
    contact_schema: strawberry.scalars.JSON


class ContactTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.Contact

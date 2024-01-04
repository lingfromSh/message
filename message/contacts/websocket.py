# Standard Library
import typing

# Third Party Library
from message.common.constants import ContactEnum
from message.helpers.decorators import contact_schema
from pydantic import BaseModel


@contact_schema(ContactEnum.WEBSOCKET)
class Schema(BaseModel):
    """
    Websocket schema
    """

    connection: str

# Standard Library
import typing

# Third Party Library
from pydantic import BaseModel

# First Library
from common.constants import ContactEnum
from helpers.decorators import contact_schema


@contact_schema(ContactEnum.WEBSOCKET)
class Schema(BaseModel):
    """
    Websocket schema
    """

    connection: str

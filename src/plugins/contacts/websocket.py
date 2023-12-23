# Standard Library
import typing

# Third Party Library
from pydantic import BaseModel

# First Library
from helpers.decorators import contact_schema


@contact_schema("websocket")
class Schema(BaseModel):
    """
    Websocket schema
    """

    connection_id: str

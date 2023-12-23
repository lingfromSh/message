# Standard Library
import typing

# Third Party Library
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import NameEmail

# First Library
from helpers.decorators import contact_schema


@contact_schema("email")
class Schema(BaseModel):
    """
    Email schema
    """

    email: typing.Union[EmailStr, NameEmail]

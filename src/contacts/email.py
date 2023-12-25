# Standard Library
import typing

# Third Party Library
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import NameEmail

# First Library
from common.constants import ContactEnum
from helpers.decorators import contact_schema


@contact_schema(ContactEnum.EMAIL)
class Schema(BaseModel):
    """
    Email schema
    """

    email: typing.Union[EmailStr, NameEmail]

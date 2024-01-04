# Standard Library
import typing

# Third Party Library
from message.common.constants import ContactEnum
from message.helpers.decorators import contact_schema
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import NameEmail


@contact_schema(ContactEnum.EMAIL)
class Schema(BaseModel):
    """
    Email schema
    """

    email: typing.Union[EmailStr, NameEmail]

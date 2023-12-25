# Third Party Library
from pydantic import BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber

# First Library
from common.constants import ContactEnum
from helpers.decorators import contact_schema


@contact_schema(ContactEnum.MOBILE)
class Schema(BaseModel):
    """
    Mobile schema
    """

    mobile: PhoneNumber

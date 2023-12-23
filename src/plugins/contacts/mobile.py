# Third Party Library
from pydantic import BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber

# First Library
from helpers.decorators import contact_schema


@contact_schema("mobile")
class Schema(BaseModel):
    mobile: PhoneNumber

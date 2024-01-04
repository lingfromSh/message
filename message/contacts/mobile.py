# Third Party Library
from message.common.constants import ContactEnum
from message.helpers.decorators import contact_schema
from pydantic import BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber


@contact_schema(ContactEnum.MOBILE)
class Schema(BaseModel):
    """
    Mobile schema
    """

    mobile: PhoneNumber

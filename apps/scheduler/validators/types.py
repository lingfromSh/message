from typing import Annotated

from bson.objectid import ObjectId
from pydantic import AfterValidator
from pydantic import PlainValidator

ObjectID = Annotated[
    str, AfterValidator(lambda x: ObjectId(x)), PlainValidator(lambda x: str(x))
]

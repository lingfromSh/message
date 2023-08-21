from typing import Annotated

from bson.objectid import ObjectId
from pydantic import AfterValidator
from pydantic import PlainSerializer
from pydantic import PlainValidator

from apps.endpoint.validators.endpoint import ETag
from apps.endpoint.validators.endpoint import ExID

ObjectID = Annotated[
    str, PlainValidator(lambda x: ObjectId(x)), PlainSerializer(lambda x: str(x))
]


def validate_etag(v: str):
    assert v.startswith("#etag:")
    return ETag(v[6:])


def validate_exid(v: str):
    assert v.startswith("#exid:")

    return ExID(v[6:])


EndpointTag = Annotated[ETag, PlainValidator(validate_etag)]

EndpointExID = Annotated[ExID, PlainValidator(validate_exid)]

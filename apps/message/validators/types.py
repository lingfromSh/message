from typing import Annotated, Union

from bson.objectid import ObjectId
from pydantic import AfterValidator
from pydantic import PlainSerializer
from pydantic import WrapSerializer
from pydantic import PlainValidator
from pydantic import ValidationError

from apps.endpoint.validators.endpoint import ETag
from apps.endpoint.validators.endpoint import ExID


def validate_objectid(v: Union[str, ObjectId]):
    assert isinstance(v, (str, ObjectId))
    return ObjectId(v) if isinstance(v, str) else v


def validate_etag(v: str):
    assert v.startswith("#etag:")
    return ETag(v[6:])


def validate_exid(v: str):
    assert v.startswith("#exid:")

    return ExID(v[6:])


EndpointTag = Annotated[ETag, PlainValidator(validate_etag)]

EndpointExID = Annotated[ExID, PlainValidator(validate_exid)]

ObjectID = Annotated[
    ObjectId, PlainValidator(validate_objectid), PlainSerializer(lambda x: str(x))
]

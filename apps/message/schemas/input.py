import dataclasses
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import strawberry

from apps.message.common.constants import MessageProviderType
from apps.message.validators.provider import CreateProviderInputModel
from apps.message.validators.provider import DestroyProviderInputModel
from apps.message.validators.provider import UpdateProviderInputModel
from infrastructures.graphql import ObjectID


@strawberry.input
class CreateProviderInput:
    type: strawberry.enum(MessageProviderType)
    code: str
    name: str
    config: Optional[strawberry.scalars.JSON] = None

    def to_pydantic(self) -> CreateProviderInputModel:
        data = dataclasses.asdict(self)
        return CreateProviderInputModel.model_validate(data)


@strawberry.input
class UpdateProviderInput:
    oid: ObjectID
    type: Optional[strawberry.enum(MessageProviderType)]
    code: Optional[str]
    name: Optional[str]
    config: Optional[strawberry.scalars.JSON] = None

    def to_pydantic(self) -> UpdateProviderInputModel:
        data = dataclasses.asdict(self)
        return UpdateProviderInputModel.model_validate(data)


@strawberry.input
class DestroyProviderInput:
    oids: List[ObjectID]

    def to_pydantic(self) -> DestroyProviderInputModel:
        data = dataclasses.asdict(self)
        return DestroyProviderInputModel.model_validate(data)

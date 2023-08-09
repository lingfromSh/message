from apps.endpoint.models import Endpoint
from bson.objectid import ObjectId
from typing import Optional, List
from pydantic import EmailStr
from pydantic import model_validator
from pydantic import computed_field
from pydantic import Field
from pydantic import BaseModel
from pydantic import ConfigDict

from .types import ObjectID


class CreateEndpointInputModel(BaseModel):
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[EmailStr]]

    async def save(self):
        endpoint = Endpoint(**self.model_dump(exclude_none=True))
        await endpoint.commit()
        return endpoint


class UpdateEndpointInputModel(BaseModel):
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[EmailStr]]

    async def save(self):
        endpoint = await Endpoint.find_one({"external_id": self.external_id})
        if not endpoint:
            raise ValueError("endpoint not found")
        if self.tags is not None:
            endpoint.tags = self.tags
        if self.websockets is not None:
            endpoint.websockets = self.websockets
        if self.emails is not None:
            endpoint.emails = self.emails
        await endpoint.commit()
        return endpoint


class DestroyEndpointInputModel(BaseModel):
    oids: Optional[List[ObjectID]]
    external_ids: Optional[List[str]]

    @model_validator(mode="after")
    def ensure_at_least_one(self):
        assert self.oids or self.external_ids, "ensure at least one is set"
        return self

    async def delete(self):
        conditions = []

        if self.oids:
            conditions.append({"_id": {"$in": list(map(ObjectId, self.oids))}})

        if self.external_ids:
            conditions.append({"external_id": {"$in": self.external_ids}})

        result = await Endpoint.collection.delete_many({"$or": conditions})
        return result.deleted_count


class EndpointOutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oid: ObjectID = Field(alias="pk")
    external_id: str
    tags: Optional[List[str]]

    websockets: Optional[List[str]]
    emails: Optional[List[EmailStr]]

    @computed_field
    @property
    def global_id(self) -> str:
        return self.oid

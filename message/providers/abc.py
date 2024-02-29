# Standard Library
import typing
from datetime import datetime
from datetime import timezone
from inspect import isclass

# Third Party Library
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ProcessResult(BaseModel):
    status: typing.Literal["success", "pending", "inprocess", "failed"]
    error_message: typing.Optional[str] = Field(default=None)
    processed_at: datetime = Field(default_factory=datetime.now(timezone.utc))


class ProviderInfo(BaseModel):
    name: str
    code: str
    description: typing.Optional[str] = Field(default=None)
    supported_contacts: typing.List[str] = Field(default_factory=list)
    can_recv: bool
    can_send: bool

    connection_definition: BaseModel
    message_definition: BaseModel

    abstract: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProviderMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if "Meta" not in attrs and isclass(attrs["Meta"]):
            raise ValueError("Provider must have a Meta class")

        metacls = attrs.pop("Meta")
        if hasattr(metacls, "abstract") and metacls.abstract:
            return super().__new__(cls, name, bases, attrs)

        info = ProviderInfo.model_validate(metacls(), from_attributes=True)
        attrs["meta"] = info

        return super().__new__(cls, name, bases, attrs)


class ProviderBase(metaclass=ProviderMetaclass):
    class Meta:
        abstract = True

    def __init__(self, connection_params: typing.Union[dict, BaseModel]) -> None:
        self.connection_params = self.meta.connection_definition.model_validate(
            connection_params, from_attributes=True
        )

    async def send(self, message: BaseModel) -> ProcessResult:
        raise NotImplementedError

    async def recv(self, bulk_size: int = None) -> ProcessResult:
        raise NotImplementedError

    async def is_avaliable(self) -> bool:
        raise NotImplementedError

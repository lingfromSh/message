# Standard Library
import typing

# Third Party Library
from pydantic import BaseModel

T = typing.TypeVar("T")


# TODO: 不需要手动声明应该自动获取DATA
class JSONResponse(BaseModel, typing.Generic[T]):
    code: int = 200
    message: str = "ok"
    data: typing.Optional[T] = None

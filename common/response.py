from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Union

from sanic.compat import Header
from sanic.response import JSONResponse


class MessageJSONResponse(JSONResponse):
    def __init__(
        self,
        data: Any | None = None,
        message: Any | None = "ok",
        status: int = 200,
        headers: Header | Dict | None = None,
        content_type: str = "application/json",
        dumps: Callable[..., Any] | None = None,
        **kwargs: Any
    ):
        body = {"code": status, "data": data, "msg": message}
        super().__init__(body, status, headers, content_type, dumps, **kwargs)

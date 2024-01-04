# Future Library
from __future__ import annotations

# Standard Library
from typing import Any
from typing import Optional
from typing import Type
from typing import Union

# Third Party Library
from tortoise import Model
from tortoise.fields import Field
from ulid import ULID

__all__ = [
    "ULIDField",
]


class ULIDField(Field[ULID], ULID):
    """
    ULID Field

    This field can store ulid value.

    If used as a primary key, it will auto-generate a ULID by default.
    """

    SQL_TYPE = "CHAR(26)"

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("pk", False) and "default" not in kwargs:
            kwargs["default"] = lambda: ULID()
        super().__init__(**kwargs)

    def to_db_value(
        self, value: Any, instance: "Union[Type[Model], Model]"
    ) -> Optional[str]:
        return value and str(value)

    def to_python_value(self, value: Any) -> Optional[ULID]:
        if value is None or isinstance(value, ULID):
            return value
        return ULID.from_str(value)

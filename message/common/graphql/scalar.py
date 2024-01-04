# Standard Library
from typing import NewType

# Third Party Library
import strawberry
from ulid import ULID as _ULID

ULID = strawberry.scalar(
    NewType("ULID", _ULID),
    description="Universally Unique Lexicographically Sortable Identifier (ULID)",
    specified_by_url="https://github.com/ulid/spec",
    serialize=lambda v: ULID.from_str(v),
    parse_value=lambda v: str(v),
)

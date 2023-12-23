# Standard Library
import typing

# Third Party Library
import aiofiles
import rtoml


async def read_toml(path: str) -> typing.Any:
    async with aiofiles.open(path, "r") as f:
        return rtoml.load(await f.read())

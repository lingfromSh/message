# Standard Library
from functools import wraps
from inspect import isasyncgenfunction
from inspect import iscoroutinefunction

# Third Party Library
from message.infra import infra_check


def ensure_infra(*infra_names: list[str], raise_exceptions: bool = True):
    def wrapper(func):
        if iscoroutinefunction(func):

            @wraps(func)
            async def wrapped(*args, **kwargs):
                if await infra_check(*infra_names, raise_exceptions=raise_exceptions):
                    return await func(*args, **kwargs)

            return wrapped

        elif isasyncgenfunction(func):

            @wraps(func)
            async def wrapped(*args, **kwargs):
                if await infra_check(*infra_names, raise_exceptions=raise_exceptions):
                    for item in await func(*args, **kwargs):
                        yield item

            return wrapped

        else:

            @wraps(func)
            async def wrapped(*args, **kwargs):
                if await infra_check(*infra_names, raise_exceptions=raise_exceptions):
                    return func(*args, **kwargs)

            return wrapped

    return wrapper

# Standard Library
from functools import wraps
from inspect import isasyncgenfunction
from inspect import iscoroutinefunction
from inspect import isfunction
from inspect import isgeneratorfunction

# First Library
from common.constants import ContactEnum
from infra import infra_check
from infra import sync_infra_check


def contact_schema(code: ContactEnum):
    """
    Decorator to define a contact schema
    """
    # First Library
    from mixins.contact import ContactMixin

    def wrapper(cls):
        ContactMixin.register_schema(code, schema=cls)
        return cls

    return wrapper


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

        elif isfunction(func):

            @wraps(func)
            def wrapped(*args, **kwargs):
                if sync_infra_check(*infra_names, raise_exceptions=raise_exceptions):
                    return func(*args, **kwargs)

            return wrapped

        elif isgeneratorfunction(func):

            @wraps(func)
            def wrapped(*args, **kwargs):
                if sync_infra_check(*infra_names, raise_exceptions=raise_exceptions):
                    for item in func(*args, **kwargs):
                        yield item

            return wrapped

    return wrapper

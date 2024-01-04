# Standard Library
import typing
from enum import Enum
from inspect import isclass

# Third Party Library
import ulid
from message.common.graphql.scalar import ULID
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from strawberry.scalars import JSON


def convert_python_type_to_pure_python_type(python_type) -> typing.Type:
    """
    :param pydantic_model:
    :return:
    """
    model = python_type
    if isclass(model) and issubclass(model, BaseModel):
        defaults = {}
        annotations = {}
        model: BaseModel
        for name, field in model.model_fields.items():
            if default := field.get_default():
                if default != PydanticUndefined:
                    defaults[name] = default

            annotations[name] = convert_python_type_to_pure_python_type(
                field.annotation
            )

        return type(
            f"{model.__name__}Converted",
            (object,),
            dict(
                __annotations__=annotations,
                __origin__=model,
                **defaults,
            ),
        )

    origin, args = typing.get_origin(python_type) or python_type, typing.get_args(
        python_type
    )
    if origin in (
        typing.List,
        typing.Tuple,
        typing.Set,
        typing.Union,
        typing.Optional,
        list,
        tuple,
        set,
    ):
        if args:
            return origin[
                *(convert_python_type_to_pure_python_type(arg) for arg in args)
            ]
        return python_type

    if origin == typing.Literal:
        return Enum(f"Enum{ulid.ULID()}", zip(args, args))

    if origin in (typing.Any, typing.Dict, dict):
        return JSON

    if origin == ulid.ULID:
        return ULID

    return python_type

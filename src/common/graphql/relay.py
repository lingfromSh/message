# Standard Library
import math
import typing
from typing import Any

# Third Party Library
import strawberry
from strawberry.relay import Connection
from strawberry.relay import Node
from strawberry.relay import NodeID
from strawberry.relay import NodeType
from strawberry.type import StrawberryContainer
from strawberry.type import get_object_definition
from strawberry.types.info import Info
from strawberry.utils.await_maybe import AwaitableOrValue
from tortoise import Model
from tortoise.contrib.pydantic.creator import pydantic_model_creator
from tortoise.contrib.pydantic.creator import pydantic_queryset_creator
from tortoise.queryset import QuerySet

# First Library
from common.graphql.converter import convert_python_type_to_pure_python_type
from common.graphql.scalar import ULID


class MetaOptions:
    __slots__ = ("model", "abstract", "interfaces")

    def __init__(
        self,
        model: Model,
        *,
        abstract: bool = False,
        interfaces: typing.Tuple[typing.Type[object]] = None,
    ):
        assert abstract or issubclass(
            model, Model
        ), "model must be a tortoise orm model"
        self.model = model
        self.abstract = abstract
        self.interfaces = interfaces if interfaces else (_DefaultTortoiseNode,)

    @classmethod
    def from_class(cls, metacls):
        model = getattr(metacls, "model", None)
        abstract = getattr(metacls, "abstract", False)
        interfaces = getattr(metacls, "interfaces", None)
        return cls(model, abstract=abstract, interfaces=interfaces)


class TortoiseORMModelNodeMetaclass(type):
    def get_meta_from_bases(self, bases):
        for base in bases:
            if hasattr(base, "Meta"):
                return base.Meta
        return None

    def __new__(cls, name, bases, attrs):
        metacls = attrs.get("Meta") or cls.get_meta_from_bases(bases)
        options = MetaOptions.from_class(metacls)

        if options.abstract:
            return super().__new__(cls, name, bases, attrs)

        assert (
            options.model._meta.abstract is False
        ), "model must not be an abstract tortoise orm model"

        tortoise_model = options.model

        # make new name
        name = "{model_name}TortoiseNode".format(model_name="User")
        # make new bases
        pydantic_model = pydantic_model_creator(tortoise_model)
        pydantic_queryset_model = pydantic_queryset_creator(tortoise_model)
        pure_python_type = convert_python_type_to_pure_python_type(pydantic_model)
        if options.interfaces:
            bases = options.interfaces + bases
        # NOTE: inherit from pure_python_type for inheriting fields with defaults
        bases = (pure_python_type,) + bases
        # make new attrs
        attrs["__tortoise_model__"] = tortoise_model
        attrs["__pydantic_model__"] = pydantic_model
        attrs["__pydantic_queryset_model__"] = pydantic_queryset_model
        attrs["__annotations__"] = pure_python_type.__annotations__
        attrs["__annotations__"]["id"] = NodeID[ULID]

        subcls = super().__new__(cls, name, bases, attrs)
        return strawberry.type(description="An relay node for tortoise orm model")(
            subcls
        )


@strawberry.interface(name="TortoiseNode")
class _DefaultTortoiseNode(Node):
    @classmethod
    def resolve_nodes(
        cls, *, info: Info, node_ids: typing.Iterable[ULID], required: bool = False
    ):
        # TODO: use proper dataloader from info["context"] instead
        async def resolver():
            qs = cls.__tortoise_model__.active_objects.filter(id__in=list(node_ids))
            qs_model = await cls.__pydantic_queryset_model__.from_queryset(qs)
            if qs_model.root:
                return [cls(**model.model_dump()) for model in qs_model.root]
            raise Exception(f"{cls.__tortoise_model__.__name__} not found")

        return resolver()


class TortoiseORMNode(metaclass=TortoiseORMModelNodeMetaclass):
    @classmethod
    def resolve_orm(cls, orm) -> typing.Self:
        resolved = cls.__pydantic_model__.from_orm(orm)
        return cls(**resolved.model_dump())

    class Meta:
        abstract = True


@strawberry.type
class PaginationPageInfo:
    item_total: int
    page_total: int
    current_page: int
    current_page_size: int


@strawberry.type
class TortoiseORMPaginationConnection(Connection[NodeType]):
    page_info: PaginationPageInfo = strawberry.field(description="Page info of query")

    @classmethod
    def resolve_node(
        cls, node: Model, *, info: Info, node_type: typing.Type[NodeType], **kwargs: Any
    ) -> NodeType:
        """The identity function for the node.

        This method is used to resolve a node of a different type to the
        connection's `NodeType`.

        By default it returns the node itself, but subclasses can override
        this to provide a custom implementation.

        Args:
            node:
                The resolved node which should return an instance of this
                connection's `NodeType`
            info:
                The strawberry execution info resolve the type name from

        """
        # TODO: get field type and resolve model as field type
        return node_type(**node_type.__pydantic_model__.from_orm(node).model_dump())

    @classmethod
    def resolve_connection(
        cls,
        nodes: QuerySet[Model],
        *,
        info: Info,
        page: typing.Optional[int] = None,
        page_size: typing.Optional[int] = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[typing.Self]:
        default_page_size = info.schema.config.relay_default_page_size
        max_results = info.schema.config.relay_max_results

        if isinstance(page, int):
            if page < 0:
                raise ValueError("Argument 'page' must be a non-negative integer.")
        else:
            page = 1

        if isinstance(page_size, int):
            if page_size < 0:
                raise ValueError("Argument 'page_size' must be a non-negative integer.")

            if page_size > max_results:
                page_size = max_results
        else:
            page_size = default_page_size

        type_def = get_object_definition(cls)
        node_type = type_def.type_var_map["NodeType"]
        assert type_def
        field_def = type_def.get_field("edges")
        assert field_def
        field = field_def.resolve_type(type_definition=type_def)
        while isinstance(field, StrawberryContainer):
            field = field.of_type

        edge_class = typing.cast(strawberry.relay.Edge[NodeType], field)

        async def resolver(nodes: QuerySet[Model]):
            item_total = await nodes.count()
            page_total = math.ceil(item_total / page_size)

            limit = page_size
            offset = (page - 1) * page_size

            # TODO: use dataloader to optimize problems about fetching related
            nodes = nodes.limit(limit).offset(offset)
            edges: typing.List[strawberry.relay.Edge] = [
                edge_class.resolve_edge(
                    cls.resolve_node(node, info=info, node_type=node_type, **kwargs),
                    cursor=str(node.id),
                )
                for node in (
                    await node_type.__pydantic_queryset_model__.from_queryset(nodes)
                ).root
            ]

            return cls(
                edges=edges,
                page_info=PaginationPageInfo(
                    item_total=item_total,
                    page_total=page_total,
                    current_page=page,
                    current_page_size=page_size,
                ),
            )

        return resolver(nodes)


# TODO: TortoiseORMCursorConnection(Connection[NodeType])

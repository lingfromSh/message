# Standard Library
import dataclasses
import datetime
import inspect
import math
import typing

# Third Party Library
import strawberry
from message.common.graphql.converter import convert_python_type_to_pure_python_type
from message.common.graphql.scalar import ULID
from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.field import StrawberryField
from strawberry.relay import Connection
from strawberry.relay import Node
from strawberry.relay import NodeID
from strawberry.relay import NodeType
from strawberry.relay.exceptions import RelayWrongAnnotationError
from strawberry.relay.exceptions import RelayWrongResolverAnnotationError
from strawberry.type import StrawberryContainer
from strawberry.type import get_object_definition
from strawberry.types.info import Info
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.typing import eval_type
from tortoise import Model
from tortoise.contrib.pydantic.creator import pydantic_model_creator
from tortoise.contrib.pydantic.creator import pydantic_queryset_creator
from tortoise.queryset import QuerySet


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
        name = "{model_name}TortoiseNode".format(model_name=tortoise_model.__name__)
        # make new bases
        # TODO: resolve relation fields
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
        attrs["__annotations__"]["id"] = NodeID[int]

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
    async def resolve_orm(cls, orm) -> typing.Self:
        await orm.refresh_from_db()
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


@strawberry.type(description="A connection to a list of objects")
class TortoiseORMPaginationConnection(Connection[NodeType]):
    page_info: PaginationPageInfo = strawberry.field(description="Page info of query")

    @classmethod
    def resolve_node(
        cls,
        node: Model,
        *,
        info: Info,
        node_type: typing.Type[NodeType],
        **kwargs: typing.Any,
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
        return node_type(
            **node_type.__pydantic_model__.model_validate(node).model_dump()
        )

    @classmethod
    def resolve_connection(
        cls,
        nodes: QuerySet[Model],
        *,
        info: Info,
        page: typing.Optional[int] = None,
        page_size: typing.Optional[int] = None,
        created_at_before: typing.Optional[datetime.datetime] = None,
        created_at_after: typing.Optional[datetime.datetime] = None,
        updated_at_before: typing.Optional[datetime.datetime] = None,
        updated_at_after: typing.Optional[datetime.datetime] = None,
        **kwargs,
    ) -> AwaitableOrValue[typing.Self]:
        """Resolve a connection from the list of nodes.

        This uses the described Relay Pagination algorithm_

        Args:
            info:
                The strawberry execution info resolve the type name from
            nodes:
                An iterable/iteretor of nodes to paginate
            created_at_before:
                Filter nodes created before this time
            created_at_after:
                Filter nodes created after this time
            updated_at_before:
                Filter nodes updated before this time
            updated_at_after:
                Filter nodes updated after this time

        """
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

        common_filter = {}
        if created_at_before:
            common_filter["created_at__lt"] = created_at_before
        if created_at_after:
            common_filter["created_at__gt"] = created_at_after
        if updated_at_before:
            common_filter["updated_at__lt"] = updated_at_before
        if updated_at_after:
            common_filter["updated_at__gt"] = updated_at_after

        async def resolver(nodes: QuerySet[Model]):
            item_total = await nodes.count()
            page_total = math.ceil(item_total / page_size)

            limit = page_size
            offset = (page - 1) * page_size

            # TODO: use dataloader to optimize problems about fetching related
            nodes = nodes.filter(**common_filter)
            nodes = nodes.limit(limit).offset(offset).order_by("-created_at")
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
class TortoiseORMPaginationConnectionExtension(
    strawberry.relay.fields.ConnectionExtension
):
    def apply(self, field: StrawberryField) -> None:
        field.arguments = [
            *field.arguments,
            StrawberryArgument(
                python_name="page",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(typing.Optional[int]),
                default=1,
            ),
            StrawberryArgument(
                python_name="page_size",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(typing.Optional[int]),
                default=10,
            ),
            StrawberryArgument(
                python_name="created_at_before",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    typing.Optional[datetime.datetime]
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="created_at_after",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    typing.Optional[datetime.datetime]
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="updated_at_before",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    typing.Optional[datetime.datetime]
                ),
                default=None,
            ),
            StrawberryArgument(
                python_name="updated_at_after",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    typing.Optional[datetime.datetime]
                ),
                default=None,
            ),
        ]

        f_type = field.type
        if not isinstance(f_type, type) or not issubclass(f_type, Connection):
            raise RelayWrongAnnotationError(field.name, typing.cast(type, field.origin))

        assert field.base_resolver
        # TODO: We are not using resolver_type.type because it will call
        # StrawberryAnnotation.resolve, which will strip async types from the
        # type (i.e. AsyncGenerator[Fruit] will become Fruit). This is done there
        # for subscription support, but we can't use it here. Maybe we can refactor
        # this in the future.
        resolver_type = field.base_resolver.signature.return_annotation
        if isinstance(resolver_type, str):
            resolver_type = typing.ForwardRef(resolver_type)
        if isinstance(resolver_type, typing.ForwardRef):
            resolver_type = eval_type(
                resolver_type,
                field.base_resolver._namespace,
                None,
            )

        origin = typing.get_origin(resolver_type)
        if origin is None or not issubclass(
            origin,
            (
                typing.Iterator,
                typing.Iterable,
                typing.AsyncIterator,
                typing.AsyncIterable,
            ),
        ):
            raise RelayWrongResolverAnnotationError(field.name, field.base_resolver)

        self.connection_type = typing.cast(typing.Type[Connection[Node]], field.type)

    def resolve(
        self,
        next_,
        source: typing.Any,
        info: Info,
        *,
        created_at_before: typing.Optional[datetime.datetime] = None,
        created_at_after: typing.Optional[datetime.datetime] = None,
        updated_at_before: typing.Optional[datetime.datetime] = None,
        updated_at_after: typing.Optional[datetime.datetime] = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        assert self.connection_type is not None
        return self.connection_type.resolve_connection(
            typing.cast(typing.Iterable[Node], next_(source, info, **kwargs)),
            info=info,
            created_at_before=created_at_before,
            created_at_after=created_at_after,
            updated_at_before=updated_at_before,
            updated_at_after=updated_at_after,
        )

    async def resolve_async(
        self,
        next_,
        source: typing.Any,
        info: Info,
        *,
        page: typing.Optional[int] = 1,
        page_size: typing.Optional[int] = 10,
        created_at_before: typing.Optional[datetime.datetime] = None,
        created_at_after: typing.Optional[datetime.datetime] = None,
        updated_at_before: typing.Optional[datetime.datetime] = None,
        updated_at_after: typing.Optional[datetime.datetime] = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        assert self.connection_type is not None
        nodes = next_(source, info, **kwargs)
        # nodes might be an AsyncIterable/AsyncIterator
        # In this case we don't await for it
        if inspect.isawaitable(nodes):
            nodes = await nodes

        resolved = self.connection_type.resolve_connection(
            typing.cast(typing.Iterable[Node], nodes),
            info=info,
            page=page,
            page_size=page_size,
            created_at_before=created_at_before,
            created_at_after=created_at_after,
            updated_at_before=updated_at_before,
            updated_at_after=updated_at_after,
        )

        # If nodes was an AsyncIterable/AsyncIterator, resolve_connection
        # will return a coroutine which we need to await
        if inspect.isawaitable(resolved):
            resolved = await resolved
        return resolved


def connection(
    graphql_type=None,
    *,
    resolver=None,
    name=None,
    is_subscription: bool = False,
    description=None,
    permission_classes=None,
    deprecation_reason=None,
    default=dataclasses.MISSING,
    default_factory=dataclasses.MISSING,
    metadata=None,
    directives=(),
    extensions=(),  # type: ignore
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
):
    f = StrawberryField(
        python_name=None,
        graphql_name=name,
        description=description,
        type_annotation=StrawberryAnnotation.from_annotation(graphql_type),
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives or (),
        extensions=[*extensions, TortoiseORMPaginationConnectionExtension()],
    )
    if resolver is not None:
        f = f(resolver)
    return f

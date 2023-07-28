import dataclasses
import inspect
import itertools
import math
from collections.abc import AsyncIterable
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import AsyncIterable
from typing import AsyncIterator
from typing import ForwardRef
from typing import Iterable
from typing import Iterator
from typing import List
from typing import NewType
from typing import Optional
from typing import Self
from typing import Sequence
from typing import Type
from typing import Union
from typing import cast

import orjson
import strawberry
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCursor
from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.field_extension import AsyncExtensionResolver
from strawberry.extensions.field_extension import FieldExtension
from strawberry.extensions.field_extension import SyncExtensionResolver
from strawberry.field import _RESOLVER_TYPE
from strawberry.field import field
from strawberry.http import GraphQLHTTPResponse
from strawberry.relay import Connection
from strawberry.relay import Node
from strawberry.relay.exceptions import RelayWrongAnnotationError
from strawberry.relay.exceptions import RelayWrongResolverAnnotationError
from strawberry.relay.types import NodeIterableType
from strawberry.relay.types import NodeType
from strawberry.sanic.views import GraphQLView
from strawberry.schema.config import StrawberryConfig
from strawberry.type import StrawberryContainer
from strawberry.type import get_object_definition
from strawberry.types.info import Info  # noqa: TCH001
from strawberry.utils.aio import aislice
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry.utils.inspect import in_async_context
from strawberry.utils.typing import eval_type
from typing_extensions import get_origin


async def alen(i: Union[AsyncIterable, AsyncIterator]) -> int:
    c = 0
    async for _ in i:
        c += 1
    return c


@dataclass
class MessageGraphQLConfig(StrawberryConfig):
    relay_min_page_size: int = field(default=5)
    relay_default_page_size: int = field(default=20)
    relay_max_page_size: int = field(default=500)


class MessageGraphQLView(GraphQLView):
    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return orjson.dumps(response_data, option=orjson.OPT_INDENT_2)


ObjectID = strawberry.scalar(
    NewType("ObjectID", str),
    description="The `ObjectID` scalar type represents ObjectId in MongoDB.",
    serialize=lambda v: str(v),
    parse_value=lambda v: ObjectId(v),
)


@strawberry.type(description="Information to aid in pagination.")
class MessagePageInfo:
    has_next_page: bool = field(
        description="When paginating forwards, are there more items?",
    )
    has_previous_page: bool = field(
        description="When paginating backwards, are there more items?",
    )
    current_page: int = field(description="Page number")
    current_page_size: int = field(description="Page size")
    total_page_count: int = field(description="Total count of pages")
    total_item_count: int = field(description="Total count of items")


@strawberry.type(description="list of items")
class MessageConnection(Connection[NodeType]):
    page_info: MessagePageInfo = field(
        description="Pagination data for this connection",
    )
    edges: List[NodeType] = field(
        description="Contains the nodes in this connection",
    )

    @classmethod
    def resolve_node(cls, v, *, info, **kwargs):
        type_def = get_object_definition(cls)
        assert type_def
        field_def = type_def.get_field("edges")
        assert field_def

        field = field_def.resolve_type(type_definition=type_def)
        while isinstance(field, StrawberryContainer):
            field = field.of_type

        return field._pydantic_type.model_validate(v)

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> AwaitableOrValue[Self]:
        default_page_size = info.schema.config.relay_default_page_size
        min_page_size = info.schema.config.relay_min_page_size
        max_page_size = info.schema.config.relay_max_page_size

        if page is None:
            page = 1
        elif not isinstance(page, int) or page < 1:
            raise ValueError("Argument 'page' must be non-negative integer")

        if page_size is None:
            page_size = default_page_size
        elif isinstance(page_size, int):
            page_size = min(max(page_size, min_page_size), max_page_size)
        else:
            raise ValueError(
                "Argument 'page_size' must be non-negative integer between {} and {}".format(
                    min_page_size, max_page_size
                )
            )

        type_def = get_object_definition(cls)
        assert type_def
        field_def = type_def.get_field("edges")
        assert field_def

        field = field_def.resolve_type(type_definition=type_def)
        while isinstance(field, StrawberryContainer):
            field = field.of_type

        if isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context():

            async def resolver():
                # optimization for mongodb query
                start = (page - 1) * page_size
                end = page * page_size

                if isinstance(nodes, AsyncIOMotorCursor):
                    # add limit and offset for query to reduce query size
                    total_item_count = (
                        await nodes.document_cls.collection.count_documents(
                            nodes.raw_cursor.delegate._Cursor__spec
                        )
                    )
                else:
                    total_item_count = await alen(nodes)

                total_page_count = math.ceil(total_item_count / page_size)
                try:
                    if isinstance(nodes, AsyncIOMotorCursor):
                        iterator = (
                            cast(AsyncIOMotorCursor, nodes).limit(page_size).skip(start)
                        )
                    else:
                        iterator = cast(
                            Union[AsyncIterator[NodeType], AsyncIterable[NodeType]],
                            cast(Sequence, nodes)[start:end],
                        )
                except TypeError:
                    assert isinstance(nodes, (AsyncIterator, AsyncIterable))
                    iterator = aislice(nodes, start, end)

                assert isinstance(iterator, (AsyncIterator, AsyncIterable))

                edges: List[NodeType] = [
                    cls.resolve_node(v, info=info) async for v in iterator
                ]

                has_previous_page = page > 1
                has_next_page = page < total_page_count

                return cls(
                    edges=edges,
                    page_info=MessagePageInfo(
                        has_previous_page=has_previous_page,
                        has_next_page=has_next_page,
                        current_page=page,
                        current_page_size=page_size,
                        total_page_count=total_page_count,
                        total_item_count=total_item_count,
                    ),
                )

            return resolver()

        start = (page - 1) * page_size
        end = page * page_size
        total_item_count = len(nodes)
        total_page_count = math.ceil(total_item_count / page_size)
        try:
            iterator = cast(
                Union[Iterator[NodeType], Iterable[NodeType]],
                cast(Sequence, nodes)[start:end],
            )
        except TypeError:
            assert isinstance(nodes, (Iterable, Iterator))
            iterator = itertools.islice(
                nodes,
                start,
                end,
            )

        edges = [cls.resolve_node(v, info=info) for v in iterator]

        has_previous_page = page > 1
        has_next_page = page < total_page_count

        return cls(
            edges=edges,
            page_info=MessagePageInfo(
                has_previous_page=has_previous_page,
                has_next_page=has_next_page,
                current_page=page,
                current_page_size=page_size,
                total_page_count=total_page_count,
                total_item_count=total_item_count,
            ),
        )


class MessageConnectionExtension(strawberry.relay.fields.ConnectionExtension):
    connection_type: Type[MessageConnection[NodeType]]

    def apply(self, field) -> None:
        field.arguments = [
            *field.arguments,
            strawberry.arguments.StrawberryArgument(
                python_name="page",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
                description=("Current page"),
                default=1,
            ),
            strawberry.arguments.StrawberryArgument(
                python_name="page_size",
                graphql_name=None,
                type_annotation=StrawberryAnnotation(Optional[int]),
                description=("Page size"),
                default=None,
            ),
        ]

        f_type = field.type
        if not isinstance(f_type, type) or not issubclass(f_type, Connection):
            raise RelayWrongAnnotationError(field.name, cast(type, field.origin))

        assert field.base_resolver
        # TODO: We are not using resolver_type.type because it will call
        # StrawberryAnnotation.resolve, which will strip async types from the
        # type (i.e. AsyncGenerator[Fruit] will become Fruit). This is done there
        # for subscription support, but we can't use it here. Maybe we can refactor
        # this in the future.
        resolver_type = field.base_resolver.signature.return_annotation
        if isinstance(resolver_type, str):
            resolver_type = ForwardRef(resolver_type)
        if isinstance(resolver_type, ForwardRef):
            resolver_type = eval_type(
                resolver_type,
                field.base_resolver._namespace,
                None,
            )

        origin = get_origin(resolver_type)
        if origin is None or not issubclass(
            origin, (Iterator, Iterable, AsyncIterator, AsyncIterable)
        ):
            raise RelayWrongResolverAnnotationError(field.name, field.base_resolver)

        self.connection_type = cast(Type[Connection[Node]], field.type)

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        *,
        page: Optional[str] = None,
        page_size: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        return self.connection_type.resolve_connection(
            cast(Iterable[Node], next_(source, info, **kwargs)),
            info=info,
            page=page,
            page_size=page_size,
        )

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        *,
        page: Optional[str] = None,
        page_size: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        assert self.connection_type is not None
        nodes = next_(source, info, **kwargs)
        # nodes might be an AsyncIterable/AsyncIterator
        # In this case we don't await for it
        if inspect.isawaitable(nodes):
            nodes = await nodes

        resolved = self.connection_type.resolve_connection(
            cast(Iterable[Node], nodes),
            info=info,
            page=page,
            page_size=page_size,
        )

        # If nodes was an AsyncIterable/AsyncIterator, resolve_connection
        # will return a coroutine which we need to await
        if inspect.isawaitable(resolved):
            resolved = await resolved
        return resolved


def connection(
    graphql_type: Optional[Type[Connection[NodeType]]] = None,
    *,
    resolver=None,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes=None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory=dataclasses.MISSING,
    metadata=None,
    directives: Optional[Sequence[object]] = (),
    extensions: List[FieldExtension] = (),  # type: ignore
    # This init parameter is used by pyright to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
) -> Any:
    """Annotate a property or a method to create a relay connection field.

    Relay connections are mostly used for pagination purposes. This decorator
    helps creating a complete relay endpoint that provides default arguments
    and has a default implementation for the connection slicing.

    Note that when setting a resolver to this field, it is expected for this
    resolver to return an iterable of the expected node type, not the connection
    itself. That iterable will then be paginated accordingly. So, the main use
    case for this is to provide a filtered iterable of nodes by using some custom
    filter arguments.

    Examples:
        Annotating something like this:

        >>> @strawberry.type
        >>> class X:
        ...     some_node: relay.Connection[SomeType] = relay.connection(
                    resolver=get_some_nodes,
        ...         description="ABC",
        ...     )
        ...
        ...     @relay.connection(relay.Connection[SomeType], description="ABC")
        ...     def get_some_nodes(self, age: int) -> Iterable[SomeType]:
        ...         ...

        Will produce a query like this:

        ```
        query {
            someNode (
                before: String
                after: String
                first: String
                after: String
                age: Int
            ) {
                totalCount
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
                edges {
                    cursor
                    node {
                        id
                        ...
                    }
                }
            }
        }
        ```

    .. _Relay connections:
        https://relay.dev/graphql/connections.htm

    """
    f = strawberry.relay.fields.StrawberryField(
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
        extensions=[*extensions, MessageConnectionExtension()],
    )
    if resolver is not None:
        f = f(resolver)
    return f

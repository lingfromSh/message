import orjson
from strawberry.relay import Node, NodeID
from strawberry.http import GraphQLHTTPResponse
from strawberry.sanic.views import GraphQLView


class MessageGraphQLView(GraphQLView):
    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return orjson.dumps(response_data, option=orjson.OPT_INDENT_2)


class MessageRelayNode(Node):
    global_id: NodeID[str]

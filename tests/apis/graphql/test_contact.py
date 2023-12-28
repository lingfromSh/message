# Standard Library
import typing

# Third Party Library
import gql
import pytest
import stringcase
from assertpy import assert_that
from gql.transport.aiohttp import AIOHTTPTransport


# FIXME: fix tests
@pytest.fixture(scope="package")
def config():
    return {
        "schema_endpoint": "http://localhost:8000/graphql",
    }


@pytest.fixture(scope="package")
def client(config):
    transport = AIOHTTPTransport(url=config["schema_endpoint"])
    client = gql.Client(transport=transport, fetch_schema_from_transport=True)
    return client


@pytest.fixture(scope="session")
def graphql_schema():
    def wrapper(schema_name: typing.Literal["contact"]):
        with open(f"tests/apis/graphql/schemas/{schema_name}.graphql", "r") as fp:
            return fp.read()

    return wrapper


@pytest.fixture(scope="session")
def contact_schema(graphql_schema):
    return graphql_schema(schema_name="contact")


def build_variables(**kwargs):
    variables = {}
    for k, v in kwargs.items():
        variables[stringcase.camelcase(k)] = v

    return variables


def contact_node_assert(node):
    assert_that(node).contains_key(
        "id",
        "name",
        "code",
        "description",
        "definition",
        "createdAt",
        "updatedAt",
    )
    assert_that(node["id"]).is_type_of(str)
    assert_that(node["name"]).is_type_of(str)
    assert_that(node["code"]).is_type_of(str)
    assert_that(node["description"]).is_type_of(str)
    assert_that(node["definition"]).is_type_of(dict)
    assert_that(node["createdAt"]).is_type_of(str)
    assert_that(node["updatedAt"]).is_type_of(str)


async def contact_query(client, contact_schema, operation_name, **kwargs):
    doc = gql.gql(contact_schema)
    variables = build_variables(**kwargs)
    result = await client.execute_async(
        doc, operation_name=operation_name, variable_values=variables
    )
    return result[stringcase.camelcase(operation_name)]


@pytest.mark.asyncio
async def test_contact_query(client, contact_schema):
    result = await contact_query(client, contact_schema, "Contacts")
    assert_that(result).is_type_of(dict)
    assert_that(result).contains_key("edges")
    assert_that(result["edges"]).is_type_of(list)
    assert_that(result["edges"]).is_length(3)
    for edge in result["edges"]:
        assert_that(edge).contains_key("cursor", "node")
        contact_node_assert(edge["node"])


@pytest.mark.asyncio
async def test_contact_query_with_name(client, contact_schema):
    """
    Perform contact query with specified name.

    Args:
        client (object): The GraphQL client used for executing the query.
        contact_schema (str): The GraphQL schema for the contact query.

    Returns:
        None

    Raises:
        AssertionError: If the result is not a dictionary.
        AssertionError: If the result does not contain the key "contacts".
        AssertionError: If the "edges" key is not present in the "contacts" dictionary.
        AssertionError: If the "edges" value is not a list.
        AssertionError: If an edge object does not have the keys "cursor" and "node".
        AssertionError: If a node object does not have the keys "id", "name", "code", "description", "definition", "createdAt", and "updatedAt".
        AssertionError: If the "id" key is not of type string.
        AssertionError: If the "name" key is not of type string or does not match the specified name.
        AssertionError: If the "code" key is not of type string.
        AssertionError: If the "description" key is not of type string.
        AssertionError: If the "definition" key is not of type dictionary.
        AssertionError: If the "createdAt" key is not of type string.
        AssertionError: If the "updatedAt" key is not of type string.
    """
    names = ["Websocket", "Mobile", "Email"]
    for name in names:
        result = await contact_query(client, contact_schema, "Contacts", name=name)
        assert_that(result).is_type_of(dict)
        assert_that(result).contains_key("edges")
        assert_that(result["edges"]).is_type_of(list)
        for edge in result["edges"]:
            assert_that(edge).contains_key("cursor", "node")
            contact_node_assert(edge["node"])
            assert_that(edge["node"]["name"]).is_equal_to(name)


@pytest.mark.asyncio
async def test_contact_query_with_code(client, contact_schema):
    """
    Perform contact query with specified code.

    Args:
        client (object): The GraphQL client used for executing the query.
        contact_schema (str): The GraphQL schema for the contact query.

    Returns:
        None

    Raises:
        AssertionError: If the result is not a dictionary.
        AssertionError: If the result does not contain the key "contacts".
        AssertionError: If the "edges" key is not present in the "contacts" dictionary.
        AssertionError: If the "edges" value is not a list.
        AssertionError: If an edge object does not have the keys "cursor" and "node".
        AssertionError: If a node object does not have the keys "id", "name", "code", "description", "definition", "createdAt", and "updatedAt".
        AssertionError: If the "id" key is not of type string.
        AssertionError: If the "name" key is not of type string.
        AssertionError: If the "code" key is not of type string or does not match the specified code.
        AssertionError: If the "description" key is not of type string.
        AssertionError: If the "definition" key is not of type dictionary.
        AssertionError: If the "createdAt" key is not of type string.
        AssertionError: If the "updatedAt" key is not of type string.
    """
    codes = ["websocket", "mobile", "email"]
    for code in codes:
        result = await contact_query(client, contact_schema, "Contacts", code=code)
        assert_that(result).is_type_of(dict)
        assert_that(result).contains_key("edges")
        assert_that(result["edges"]).is_type_of(list)
        for edge in result["edges"]:
            assert_that(edge).contains_key("cursor", "node")
            contact_node_assert(edge["node"])
            assert_that(edge["node"]["code"]).is_equal_to(code)


@pytest.mark.asyncio
async def test_contact_register(client, contact_schema):
    result = await contact_query(
        client,
        contact_schema,
        "ContactRegister",
        name="Slack",
        code="slack",
        description="Contact of Slack",
        definition={"type": "JSONSCHEMA", "contactSchema": {}},
    )
    assert_that(result).is_type_of(dict)
    contact_node_assert(result)


@pytest.mark.asyncio
async def test_contact_destory(client, contact_schema):
    result = await contact_query(client, contact_schema, "Contacts")
    ids = [edge["node"]["id"] for edge in result["contacts"]["edges"]]
    result = await contact_query(client, contact_schema, "ContactDestory", ids=ids)
    assert_that(result).is_type_of(str).is_equal_to("ok")

import environ


@environ.config(prefix="API")
class APIConfig:
    GRAPHIQL_ENABLED = environ.var(
        default=True, converter=bool, name="GRAPHIQL_ENABLED"
    )
    GRAPHQL_RELAY_DEFAULT_PAGE_SIZE = environ.var(
        default=20, converter=int, name="GRAPHQL_RELAY_DEFAULT_PAGE_SIZE"
    )
    GRAPHQL_RELAY_MIN_PAGE_SIZE = environ.var(
        default=1, converter=int, name="GRAPHQL_RELAY_MIN_PAGE_SIZE"
    )
    GRAPHQL_RELAY_MAX_PAGE_SIZE = environ.var(
        default=500, converter=int, name="GRAPHQL_RELAY_MAX_PAGE_SIZE"
    )

import environ


@environ.config(prefix="API")
class APIConfig:
    GRAPHIQL_ENABLED = environ.var(default=True, converter=bool)
    GRAPHQL_RELAY_DEFAULT_PAGE_SIZE = environ.var(default=20, converter=int)
    GRAPHQL_RELAY_MIN_PAGE_SIZE = environ.var(default=1, converter=int)
    GRAPHQL_RELAY_MAX_PAGE_SIZE = environ.var(default=500, converter=int)

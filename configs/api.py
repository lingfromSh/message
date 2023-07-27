import environ


@environ.config(prefix="API")
class APIConfig:
    GRAPHIQL_ENABLED = environ.var(
        default=True, converter=bool, name="GRAPHIQL_ENABLED"
    )

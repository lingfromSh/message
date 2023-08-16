import environ


@environ.config(prefix="CACHE")
class CacheConfig:
    SENTINEL_HOST = environ.var()
    SENTINEL_PORT = environ.var(converter=int)
    SENTINEL_PASSWORD = environ.var(None)
    MASTER_SET = environ.var()
    MASTER_PASSWORD = environ.var()

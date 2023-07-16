import environ


@environ.config(prefix="CACHE")
class CacheConfig:
    SENTINEL_HOST = environ.var("SENTINEL_HOST")
    SENTINEL_PORT = environ.var("SENTINEL_PORT", converter=int)
    SENTINEL_PASSWORD = environ.var(default=None, name="SENTINEL_PASSWORD")
    MASTER_SET = environ.var("MASTER_SET")
    MASTER_PASSWORD = environ.var("MASTER_PASSWORD")

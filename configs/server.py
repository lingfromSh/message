import environ


@environ.config(prefix="SERVER")
class ServerConfig:
    NAME = environ.var(default="Message", converter=str)
    DOMAIN = environ.var(default="localhost")

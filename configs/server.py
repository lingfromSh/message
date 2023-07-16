import environ


@environ.config(prefix="SERVER")
class ServerConfig:
    NAME = environ.var(default="Message", name="NAME", converter=str)
    DOMAIN = environ.var(default="localhost", name="DOMAIN")

import environ


@environ.config(prefix="DATABASE")
class DatabaseConfig:
    HOST = environ.var("HOST")
    PORT = environ.var("PORT", converter=int)
    PASSWORD = environ.var("PASSWORD")

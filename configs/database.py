import environ


@environ.config(prefix="DATABASE")
class DatabaseConfig:
    HOST = environ.var(name="HOST", default="mongodb-primary")
    PORT = environ.var(name="PORT", default=27017, converter=int)
    USER = environ.var(name="USER", default="communication")
    PASSWORD = environ.var(name="PASSWORD", default="communication-2023")

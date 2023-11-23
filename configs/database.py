import environ


@environ.config(prefix="DATABASE")
class DatabaseConfig:
    HOST = environ.var(default="mongodb-primary")
    PORT = environ.var(default=27017, converter=int)
    USER = environ.var(default="communication")
    PASSWORD = environ.var(default="communication-2023")
    REPLICA_SET = environ.var(default="message-replicas", converter=str)

import environ


@environ.config(prefix="QUEUE")
class QueueConfig:
    HOST = environ.var("HOST")
    PORT = environ.var("PORT", converter=int)
    USERNAME = environ.var("USERNAME")
    PASSWORD = environ.var("PASSWORD")

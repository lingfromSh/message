class BaseHumanDefinedException(Exception):
    """
    To represent human-defined exceptions
    """


class ImproperlyConfiguredException(BaseHumanDefinedException):
    """
    All errors include syntax error, undefined error, etc which cause system can not start.
    """

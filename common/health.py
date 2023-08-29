import abc


class HealthChecker(metaclass=abc.ABCMeta):
    """
    An interface ask inheritors to implement check function
    """

    @abc.abstractmethod
    async def check(self) -> bool:
        raise NotImplementedError

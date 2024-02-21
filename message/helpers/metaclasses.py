class Singleton(type):
    """
    Singleton MetaClass
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        instantiate our singleton meta entry
        """
        if cls not in cls._instances:
            # we have not every built an instance before.  Build one now.
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

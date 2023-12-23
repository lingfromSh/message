def contact_schema(code: str):
    """
    Decorator to define a contact schema
    """
    # First Library
    from mixins.contact import ContactMixin

    def wrapper(cls):
        ContactMixin.register_schema(code, schema=cls)
        return cls

    return wrapper

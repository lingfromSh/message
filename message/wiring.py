# Standard Library
import typing

# Third Party Library
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

if typing.TYPE_CHECKING:
    # Third Party Library
    from message.applications.contact import ContactApplication
    from message.applications.endpoint import EndpointApplication
    from message.applications.health import HealthApplication
    from message.applications.message import MessageApplication
    from message.applications.provider import ProviderApplication
    from message.applications.provider import ProviderTemplateApplication
    from message.applications.user import UserApplication


def get_application(name: str):
    """
    Get application instance by name.
    """
    match name:
        case "contact":
            # Third Party Library
            from message.applications.contact import ContactApplication

            return ContactApplication()
        case "endpoint":
            # Third Party Library
            from message.applications.endpoint import EndpointApplication

            return EndpointApplication()
        case "health":
            # Third Party Library
            from message.applications.health import HealthApplication

            return HealthApplication()
        case "message":
            # Third Party Library
            from message.applications.message import MessageApplication

            return MessageApplication()
        case "provider":
            # Third Party Library
            from message.applications.provider import ProviderApplication

            return ProviderApplication()
        case "provider_template":
            # Third Party Library
            from message.applications.provider import ProviderTemplateApplication

            return ProviderTemplateApplication()
        case "user":
            # Third Party Library
            from message.applications.user import UserApplication

            return UserApplication()
        case _:
            raise ValueError(f"Invalid application name: {name}")


class ApplicationContainer(DeclarativeContainer):
    contact_application: typing.Callable[
        ..., "ContactApplication"
    ] = providers.Singleton(get_application, name="contact")
    endpoint_application: typing.Callable[
        ..., "EndpointApplication"
    ] = providers.Singleton(get_application, name="endpoint")
    health_application: typing.Callable[..., "HealthApplication"] = providers.Singleton(
        get_application, name="health"
    )
    message_application: typing.Callable[
        ..., "MessageApplication"
    ] = providers.Singleton(get_application, name="message")
    provider_application: typing.Callable[
        ..., "ProviderApplication"
    ] = providers.Singleton(get_application, name="provider")
    provider_template_application: typing.Callable[
        ..., "ProviderTemplateApplication"
    ] = providers.Singleton(get_application, name="provider_template")
    user_application: typing.Callable[..., "UserApplication"] = providers.Singleton(
        get_application, name="user"
    )

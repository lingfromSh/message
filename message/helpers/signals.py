# Third Party Library
from blinker import signal
from message import applications
from message.common.constants import SIGNALS
from message.worker import broker

message_create_signal = signal(SIGNALS.MESSAGE_CREATE)


@message_create_signal.connect
async def create_message(
    sender, message_id, provider_id, content, users, endpoints, contacts
):
    await background_create_message.kiq(
        message_id=message_id,
        provider_id=provider_id,
        content=content,
        users=users,
        endpoints=endpoints,
        contacts=contacts,
    )


@broker.task
async def background_create_message(
    message_id,
    provider_id,
    content,
    users,
    endpoints,
    contacts,
):
    """
    Create message
    """
    message_application = applications.MessageApplication()
    user_application = applications.UserApplication()
    endpoint_application = applications.EndpointApplication()
    provider_application = applications.ProviderApplication()
    try:
        provider = await provider_application.get_provider(id=provider_id)
    except Exception:
        raise

    if users:
        try:
            users = await (
                await user_application.get_users(conditions={"id__in": users})
            )
        except Exception:
            raise

    if endpoints:
        try:
            endpoints = await (
                await endpoint_application.get_endpoints(
                    conditions={"id__in": endpoints}
                )
            )
        except Exception:
            raise

    message = await message_application.create_message(
        id=message_id,
        provider=provider,
        content=content,
        users=users,
        endpoints=endpoints,
        contacts=contacts,
    )
    await message.provider.send_message(message)

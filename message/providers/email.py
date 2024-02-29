# Standard Library
import typing

# Third Party Library
from apprise import Apprise
from apprise import NotifyFormat
from message.providers.abc import MessageDefinition
from message.providers.abc import ProcessResult
from message.providers.abc import ProviderBase
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_serializer


class EmailConnectionDefinition(BaseModel):
    """
    Definition of connection parameters for mail server.

    Args:
        from_address (str, optional): The email address to use as the sender. Defaults to None.
        secure (bool, optional): Whether to use a secure connection. Defaults to False.
        username (str): The username to use for authentication. Required.
        password (str): The password to use for authentication. Required.
        domain (str): The domain of the email server. Required.
        port (int, optional): The port to use for the connection. Defaults to None.
    """

    from_address: typing.Optional[str] = Field(default=None)
    secure: bool = Field(default=False)
    username: str
    password: str
    domain: str
    port: typing.Optional[int] = Field(default=None)


class EmailMessageDefinition(MessageDefinition):
    """
    Definition of a email message.

    Args:
        to_addresses (List[str]): The email addresses to send the message to. Required.
        title (str): The title of the email. Required.
        content (str): The content of the email. Required.
        content_type (str, optional): The content type of the email. Defaults to "plain".
        attachments (List[str], optional): The attachments to include in the email. Defaults to None.
        cc (List[str], optional): The email addresses to cc. Defaults to None.
        bcc (List[str], optional): The email addresses to bcc. Defaults to None.
    """

    cc: typing.List[str] = Field(default_factory=list)
    bcc: typing.List[str] = Field(default_factory=list)
    to: typing.List[str] = Field(default_factory=list)
    title: str
    content: str
    content_type: typing.Literal["plain", "html"] = Field(default="plain")
    attachments: typing.List[str] = Field(default_factory=list)

    @field_serializer("cc", "bcc", "to")
    def serialize_as_query_string(v) -> str:
        """
        Parse list of items into comma-separated string as a query string
        """
        return ",".join(v)


class EmailProvider(ProviderBase):
    """
    Email provider implementation using apprise library.

    This provider allow sending email messages to endpoints.

    Full support of email, like HTML content, attachments, cc, bcc, from_address, etc.
    """

    class Meta:
        name = "Email"
        code = "email"
        description = "Email provider support all features of email, like HTML content, attachments, cc, bcc, from_address, etc."

        can_send = True
        can_recv = False

        connection_definition = EmailConnectionDefinition
        message_definition = EmailMessageDefinition

    async def send(self, message: "EmailMessageDefinition") -> ProcessResult:
        if not isinstance(message, EmailMessageDefinition):
            return ProcessResult(
                status="failed",
                error_message="`message` must be a valid instance of EmailMessageDefinition",
            )

        apprise = Apprise()

        # build notify url in format of apprise
        notify_pattern = "{protocol}://{username}:{password}@{server}"

        if self.connection_params.secure:
            protocol = "mailtos"
        else:
            protocol = "mailto"

        if self.connection_params.port:
            server = f"{self.connection_params.domain}:{self.connection_params.port}"
        else:
            server = self.connection_params.domain

        notify_url = notify_pattern.format(
            protocol=protocol,
            username=self.connection_params.username,
            password=self.connection_params.password,
            server=server,
        )

        if message.users:
            endpoint_application = self.applications.endpoint_application()
            qs = await endpoint_application.get_queryset(
                filters={
                    "user_id__in": message.users,
                    "contact__code__in": self.meta.supported_contacts,
                }
            )
            async for endpoint in qs.select_related("contact"):
                validated = await endpoint.contact.validate_endpoint_value(
                    endpoint.value
                )
                message.to.append(validated.validated_data)

        if message.endpoints:
            endpoint_application = self.applications.endpoint_application()
            qs = await endpoint_application.get_queryset(
                filters={
                    "id__in": message.endpoints,
                    "contact__code__in": self.meta.supported_contacts,
                }
            )
            async for endpoint in qs.select_related("contact"):
                validated = await endpoint.contact.validate_endpoint_value(
                    endpoint.value
                )
                message.to.append(validated.validated_data)

        queries = message.model_dump(include=("to", "cc", "bcc"))

        if from_address := self.connection_params.from_address:
            queries["from"] = from_address

        notify_url = notify_url + "?" + "&".join(f"{k}={v}" for k, v in queries.items())
        apprise.add(notify_url)

        notified = await apprise.async_notify(
            body=message.content,
            title=message.title,
            attach=message.attachments,
            body_format=(
                NotifyFormat.TEXT
                if message.content_type == "plain"
                else NotifyFormat.HTML
            ),
        )

        return ProcessResult(
            status="success" if notified else "failed",
            error_message=None if notified else "Failed to send email",
        )

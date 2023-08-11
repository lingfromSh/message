import enum
import smtplib
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ipaddress import IPv4Address
from typing import List
from typing import Optional
from typing import Union

import aiohttp
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import conint
from pydantic import field_serializer

from apps.message.common.constants import MessageProviderType
from apps.message.common.constants import MessageStatus
from apps.message.common.interfaces import Message as BaseMessage
from apps.message.common.interfaces import SendResult
from apps.message.providers.base import MessageProviderModel
from apps.message.validators.types import EndpointExID
from apps.message.validators.types import EndpointTag
from apps.message.validators.types import ETag
from apps.message.validators.types import ExID


class EmailContentType(enum.Enum):
    TEXT = "text"
    HTML = "html"


class SMTPEmailMessageProviderModel(MessageProviderModel):
    """
    A message provider for email
    """

    class Info:
        name = "smtp"
        type = MessageProviderType.EMAIL

    class Capability:
        is_enabled = True
        can_send = True

    class Config(BaseModel):
        host: IPv4Address
        port: conint(gt=0, lt=65536)

        ssl_mode: bool = False

        # if ssl_mode = False, user & pass are required
        username: Optional[str]
        password: Optional[str]

        # if ssl_mode = True, keyfile & certfile are required
        # TODO: replace str with FileUrl
        keyfile: Optional[str]
        # TODO: replace str with FileUrl
        certfile: Optional[str]

    class Message(BaseMessage):
        from_address: EmailStr
        to_addresses: List[Union[EndpointTag, EndpointExID, EmailStr]]
        cc_addresses: List[Union[EndpointTag, EndpointExID, EmailStr]]
        bcc_addresses: List[Union[EndpointTag, EndpointExID, EmailStr]]
        subject: str
        content_type: EmailContentType = EmailContentType.TEXT
        content: str = ""
        # TODO: replace str with FileUrl
        attachments: List[str]

        @field_serializer("to_addresses", "cc_addresses", "bcc_addresses")
        def serialize_address_list(self, addrs, _info):
            ret = []

            for addr in addrs:
                if isinstance(addr, ExID):
                    ret.append(addr.serialize())
                elif isinstance(addr, ETag):
                    ret.extend(addr.serialize())
                else:
                    ret.append(addr)
            return ret

    async def send(self, provider_id, message: Message, immediate=True):
        if not isinstance(message, self.message_model):
            # TODO: record failure's reason
            return

        content = MIMEMultipart()
        # username and password to login and send must be the same in office365
        content["From"] = message.from_address
        content["To"] = ",".join(message.to_addresses)
        content["Subject"] = Header(message.subject, "utf-8")
        if len(message.cc_addresses) > 0:
            content["Cc"] = ",".join(message.cc_addresses)
        if len(message.bcc_addresses) > 0:
            content["Bcc"] = ",".join(message.bcc_addresses)
        for attachment in message.attachments:
            filename = attachment["name"]
            fileurl = attachment["url"]
            att = MIMEImage(await aiohttp.get(fileurl).content)
            if ref_id := attachment.get("reference"):
                att.add_header("Content-ID", ref_id)
            else:
                att.add_header("Content-ID", filename)
            att["Content-Disposition"] = "attachment;filename={}".format(filename)
            content.attach(att)

        content.attach(MIMEText(message.content, message.content_type.value, "utf-8"))

        try:
            if self.config.ssl_mode:
                server = smtplib.SMTP_SSL(
                    host=self.config.host,
                    port=self.config.port,
                    keyfile=self.config.keyfile,
                    certfile=self.config.certfile,
                )
            else:
                server = smtplib.SMTP(host=self.config.host, port=self.config.port)
                server.login(user=self.config.username, password=self.config.password)

            server.sendmail(
                from_addr=message.from_address,
                to_addrs=message.to_addresses
                + message.cc_addresses
                + message.bcc_addresses,
                msg=content.as_bytes(),
            )
            return SendResult(
                provider_id=provider_id,
                message=message,
                status=MessageStatus.SUCCEEDED.value,
            )
        finally:
            server.quit()

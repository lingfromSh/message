import enum
import smtplib
import aiohttp
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header

from ipaddress import IPv4Address
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import conint

from apps.message.common.constants import MessageProviderType
from apps.message.providers.base import MessageProviderModel


class EmailContentType(enum.Enum):
    TEXT = "text"
    HTML = "html"


class SMTPEmailMessageProviderModel(MessageProviderModel):
    """
    A message provider for email
    """

    class Info:
        name = "SMTP"
        type = MessageProviderType.EMAIL

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

    class Message(BaseModel):
        from_address: EmailStr
        to_addresses: List[EmailStr]
        cc_addresses: List[EmailStr]
        bcc_addresses: List[EmailStr]
        subject: str
        content_type: EmailContentType = EmailContentType.TEXT
        content: str = ""
        # TODO: replace str with FileUrl
        attachments: List[str]

    async def send(self, message: Message):
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
        finally:
            server.quit()

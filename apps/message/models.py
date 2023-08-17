from umongo import Document
from umongo import fields

from utils import get_app
from common.constants import SERVER_NAME

app = get_app()


@app.ctx.doc_instance.register
class Provider(Document):
    type = fields.StringField(required=True, max_length=32)
    code = fields.StringField(required=True)
    name = fields.StringField(required=True, unique=True)
    config = fields.DictField(required=False, allow_none=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "providers"
        indexes = ("type", "code", "name", "-created_at", "-updated_at")


@app.ctx.doc_instance.register
class Message(Document):
    provider = fields.ReferenceField("Provider", required=True)
    realm = fields.DictField(required=True)
    status = fields.StringField(required=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "messages"
        indexes = ("provider", "status", "-created_at", "-updated_at")


if app.name == SERVER_NAME:
    try:
        app.add_task(Provider.ensure_indexes())
        app.add_task(Message.ensure_indexes())
    except Exception:
        pass

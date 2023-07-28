from umongo import Document
from umongo import fields
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance

from utils import get_app

app = get_app()

instance = MotorAsyncIOInstance(db=app.shared_ctx.db)


@instance.register
class Provider(Document):
    type = fields.StringField(required=True, max_length=32)
    code = fields.StringField(required=True)
    name = fields.StringField(required=True, unique=True)
    config = fields.DictField(required=False, allow_none=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "providers"


@instance.register
class Message(Document):
    provier = fields.ReferenceField("Provider", required=True)
    realm = fields.DictField(required=True)
    status = fields.StringField(required=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "messages"


app.add_task(Provider.ensure_indexes())
app.add_task(Message.ensure_indexes())

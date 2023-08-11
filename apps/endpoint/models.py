from umongo import Document
from umongo import fields

from common.constants import SERVER_NAME
from utils import get_app

app = get_app()


@app.ctx.doc_instance.register
class Endpoint(Document):
    external_id = fields.StringField(required=True, unique=True)
    tags = fields.ListField(fields.StringField(), required=False, allow_none=True)
    websockets = fields.ListField(fields.StringField(), required=False, allow_none=True)
    emails = fields.ListField(fields.EmailField(), required=False, allow_none=True)

    class Meta:
        collection_name = "endpoints"


if app.name == SERVER_NAME:
    app.add_task(Endpoint.ensure_indexes())

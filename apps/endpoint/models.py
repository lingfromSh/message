import orjson
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

    async def post_insert(self, ret):
        await app.ctx.cache.set(
            f"exid:{self.external_id}:endpoint", orjson.dumps(self.dump())
        )

    async def post_update(self, ret):
        await app.ctx.cache.set(
            f"exid:{self.external_id}:endpoint", orjson.dumps(self.dump())
        )

    async def post_delete(self, ret):
        await app.ctx.cache.delete(f"exid:{self.external_id}:endpoint")

    class Meta:
        collection_name = "endpoints"
        indexes = ("external_id", "tags", "websockets", "emails")


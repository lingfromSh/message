import orjson
from umongo import Document
from umongo import fields

from utils import get_app

app = get_app()

cache = app.ctx.infra.cache()


@app.ctx.infra.database().doc_instance.register
class Endpoint(Document):
    external_id = fields.StringField(required=True, unique=True)
    tags = fields.ListField(fields.StringField(), required=False, allow_none=True)
    websockets = fields.ListField(fields.StringField(), required=False, allow_none=True)
    emails = fields.ListField(fields.EmailField(), required=False, allow_none=True)

    async def post_insert(self, ret):
        await cache.set(f"exid:{self.external_id}:endpoint", orjson.dumps(self.dump()))

    async def post_update(self, ret):
        await cache.set(f"exid:{self.external_id}:endpoint", orjson.dumps(self.dump()))

    async def post_delete(self, ret):
        await cache.delete(f"exid:{self.external_id}:endpoint")

    class Meta:
        collection_name = "endpoints"
        indexes = ("external_id", "tags", "websockets", "emails")

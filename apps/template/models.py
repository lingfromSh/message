from umongo import Document
from umongo import fields

from utils import get_app
from apps.template.utils import generate

app = get_app()


class Template(Document):
    # built-in params
    # today - today date string
    # time - current time string

    name = fields.StringField(required=True)
    provider = fields.ReferenceField("Provider", required=True)
    content = fields.DictField(required=True)

    is_enabled = fields.BooleanField(required=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    async def render(self, context={}):
        return await generate(self.content)

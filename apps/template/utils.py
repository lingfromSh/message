import jinja2
from bson.objectid import ObjectId

from apps.template.models import Template

env = jinja2.Environment(enable_async=True)


async def generate(template_string, context={}):
    template = jinja2.Template(template_string)
    return await template.render_async(context)


async def get_db_template(id: ObjectId) -> Template:
    """Return template stored in db

    Args:
        id (ObjectId): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if not isinstance(id, ObjectId):
        id = ObjectId(id)

    template = await Template.find_one({"_id": id})
    if not template:
        raise ValueError("template not found")
    return template

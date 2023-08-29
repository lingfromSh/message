import jinja2

env = jinja2.Environment(enable_async=True)


async def generate(template_string, context={}):
    template = jinja2.Template(template_string)
    return await template.render_async(context)

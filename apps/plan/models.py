from umongo import Document
from umongo import EmbeddedDocument
from umongo import fields

from utils import get_app

app = get_app()


@app.shared_ctx.doc_instance.register
class PlanTrigger(EmbeddedDocument):
    # type is enum of PlanTriggerType
    type = fields.StringField(required=True)

    # isoformat datetime
    # human readable time
    at = fields.StringField(required=True)

    # -1 = repeat, 1 = once
    repeat_time = fields.IntegerField(required=True)


@app.shared_ctx.doc_instance.register
class SubPlan(EmbeddedDocument):
    provider = fields.ReferenceField("Provider", required=True)
    message = fields.DictField(required=True)


@app.shared_ctx.doc_instance.register
class Plan(Document):
    name = fields.StringField(required=True)

    triggers = fields.ListField(fields.EmbeddedField("PlanTrigger"), required=True)

    sub_plans = fields.ListField(fields.EmbeddedField("SubPlan"))

    is_enabled = fields.BooleanField(required=True)
    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "plans"


@app.shared_ctx.doc_instance.register
class SubPlanExecution(EmbeddedDocument):
    provider = fields.ReferenceField("Provider", required=True)
    message = fields.DictField()


@app.shared_ctx.doc_instance.register
class PlanExecution(Document):
    plan = fields.ReferenceField("Plan", required=True)
    status = fields.StringField(required=True)
    reason = fields.ListField(fields.StringField(), required=False, allow_none=True)

    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "plan_executions"

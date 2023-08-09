from umongo import Document
from umongo import EmbeddedDocument
from umongo import fields

from utils import get_app

app = get_app()


@app.ctx.doc_instance.register
class PlanTrigger(EmbeddedDocument):
    # type is enum of PlanTriggerType
    type = fields.StringField(required=True)

    # isoformat datetime
    # human readable time
    timer_at = fields.AwareDateTimeField(required=False, allow_none=True)
    repeat_at = fields.StringField(required=False, allow_none=True)
    # record last trigger time for repeat mode
    last_trigger = fields.AwareDateTimeField(required=False, allow_none=True)

    # -1 = repeat, 1 = once
    repeat_time = fields.IntegerField(required=True)

    start_time = fields.AwareDateTimeField(required=True)
    end_time = fields.AwareDateTimeField(required=False, allow_none=True)


@app.ctx.doc_instance.register
class SubPlan(EmbeddedDocument):
    provider = fields.ReferenceField("Provider", required=True)
    message = fields.DictField(required=True)


@app.ctx.doc_instance.register
class Plan(Document):
    name = fields.StringField(required=True)

    triggers = fields.ListField(fields.EmbeddedField("PlanTrigger"), required=True)

    sub_plans = fields.ListField(fields.EmbeddedField("SubPlan"))

    is_enabled = fields.BooleanField(required=True)
    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "plans"
        indexes = ["triggers.at"]


@app.ctx.doc_instance.register
class PlanExecution(Document):
    plan = fields.ReferenceField("Plan", required=True)
    status = fields.StringField(required=True)
    reason = fields.ListField(fields.StringField(), required=False, allow_none=True)

    time_to_execute = fields.AwareDateTimeField(required=True)
    created_at = fields.AwareDateTimeField(required=True)
    updated_at = fields.AwareDateTimeField(required=True)

    class Meta:
        collection_name = "plan_executions"

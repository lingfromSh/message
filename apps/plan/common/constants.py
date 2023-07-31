import enum


class PlanExecutionStatus(str, enum.Enum):
    IN_QUEUE = "in_process"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PlanTriggerType(str, enum.Enum):
    REPEAT = "repeat"
    COUNTER = "counter"
    ONCE = "once"

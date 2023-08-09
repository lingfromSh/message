import enum


class PlanExecutionStatus(str, enum.Enum):
    IN_QUEUE = "in_queue"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PlanTriggerType(str, enum.Enum):
    REPEAT = "repeat"
    TIMER = "timer"

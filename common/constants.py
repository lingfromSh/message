import enum

SERVER_NAME = "Message"
PLANNER_NAME = "Message-Planner"
EXECUTOR_NAME = "Message-Executor"
HEALTHY = True
UNHEALTHY = False

TOPIC_EXCHANGE_NAME = "message.topic.exchange"



class TopicSubscriberType(enum.Enum):
    BROADCAST = "broadcast"
    SHARED = "shared"

# Third Party Library
import taskiq_fastapi
from taskiq_redis import ListQueueBroker

broker = ListQueueBroker("redis://localhost:6379/")

taskiq_fastapi.init(broker, "message.main:app")

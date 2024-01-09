# Third Party Library
import taskiq_fastapi
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration
from message.common.constants import SETTINGS_YAML
from taskiq_aio_pika import AioPikaBroker


class DependencyContainer(DeclarativeContainer):
    config = Configuration()


dependency = DependencyContainer()
dependency.config.from_yaml(SETTINGS_YAML)


broker = AioPikaBroker(
    url=dependency.config.queue.dsn(),
    qos=dependency.config.queue.prefecth_count(),
)

taskiq_fastapi.init(broker, "message.main:app")

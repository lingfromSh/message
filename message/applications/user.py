# Third Party Library
from message import models
from message.applications.base import Application
from message.helpers.decorators import ensure_infra


class UserApplication(Application[models.User]):
    """
    User Application
    """

    model_class = models.User

    @ensure_infra("persistence")
    async def create(self, **kwargs) -> models.User:
        # TODO: Implement create user logic
        raise NotImplementedError

    @ensure_infra("persistence")
    async def get_by_external_id(self, external_id: str) -> models.User:
        """
        Get a single user by external id
        """
        return await self.model_class.active_objects.get_or_none(
            external_id=external_id
        )

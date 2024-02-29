# Third Party Library
from message import models
from message.applications.base import Application
from tortoise.queryset import QuerySet


class EndpointApplication(Application[models.Endpoint]):
    """
    Endpoint Application
    """

    # required by Application
    model_class = models.Endpoint

    async def get_queryset(
        self,
        filters: dict,
        limit: int = None,
        offset: int = None,
        order_by: tuple[str] = None,
        for_update: bool = False,
        use_index: tuple[str] = None,
        use_db: str = None,
    ) -> QuerySet[models.Endpoint]:
        # hhhhh
        return await super().get_queryset(
            filters, limit, offset, order_by, for_update, use_index, use_db
        )

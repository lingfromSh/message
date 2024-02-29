# Third Party Library
from message import models
from message.applications.base import Application
from message.helpers.decorators import ensure_infra
from message.wiring import ApplicationContainer
from tortoise.transactions import atomic


class UserApplication(Application[models.User]):
    """
    User Application
    """

    model_class = models.User

    @ensure_infra("persistence")
    @atomic()
    async def create(self, **kwargs) -> models.User:
        # TODO: Implement create user logic
        endpoints = kwargs.pop("endpoints", [])

        domain = self.model_class(**kwargs)
        await domain.validate(raise_exception=True)
        await domain.save()

        endpoint_application = ApplicationContainer.endpoint_application()
        contact_application = ApplicationContainer.contact_application()

        for endpoint in endpoints:
            if contact_id := endpoint.pop("contact_id", None):
                endpoint["contact"] = await contact_application.get(id=contact_id)
            if isinstance(endpoint["value"], str):
                endpoint["value"] = {"regex": endpoint["value"]}
            await endpoint_application.create(user=domain, **endpoint)

        return domain

    @ensure_infra("persistence")
    @atomic()
    async def update(self, domain, **kwargs) -> models.User:
        if kwargs.get("external_id", None) is not None:
            domain.external_id = kwargs["external_id"]
        if kwargs.get("metadata", None) is not None:
            domain.metadata = kwargs["metadata"]
        if endpoints := kwargs.get("endpoints", None):
            endpoint_application = ApplicationContainer.endpoint_application()
            contact_application = ApplicationContainer.contact_application()

            for endpoint in endpoints:
                # get contact if contact_id is provided
                if contact_id := endpoint.pop("contact_id", None):
                    endpoint["contact"] = await contact_application.get(contact_id)

                # drop empty endpoint value, because it's not allowed to save in database
                if not endpoint.get("value") or not isinstance(
                    endpoint.get("value"), dict
                ):
                    endpoint.pop("value", None)

                # get endpoint domain if id is provided
                if endpoint.get("id", None):
                    endpoint_domain = await endpoint_application.get(
                        id=endpoint.pop("id"),
                        user=domain,
                    )
                    if not endpoint_domain:
                        continue
                    await endpoint_application.update(endpoint_domain, **endpoint)
                else:
                    await endpoint_application.create(user=domain, **endpoint)

        await domain.save()
        return domain

    @ensure_infra("persistence")
    async def get_by_external_id(self, external_id: str) -> models.User:
        """
        Get a single user by external id
        """
        return await self.model_class.active_objects.get_or_none(
            external_id=external_id
        )

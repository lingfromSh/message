# Third Party Library
from message.exceptions.user import UserDuplicatedExternalIDError


class UserMixin:
    async def is_save(self) -> bool:
        """
        Check if user is saved.
        """
        return self._saved_in_db

    async def validate(self, raise_exception: bool = False) -> bool:
        """
        Validate user data.
        """
        qs = self.__class__.filter(external_id=self.external_id)
        if await self.is_save():
            qs = qs.exclude(id=self.id)

        if await qs.exists():
            if raise_exception:
                raise UserDuplicatedExternalIDError
            return False
        return True

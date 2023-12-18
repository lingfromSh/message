# First Library
from common.ddd import Application
from repositories.end_user import EndUserRepository


class EndUserApplication(Application):
    repository = EndUserRepository

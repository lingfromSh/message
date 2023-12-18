# Standard Library
from typing import List

# Third Party Library
from ulid import ULID

# First Library
from common.ddd import Domain
from common.ddd import Repository
from models import EndUser


class EndUserRepository(Repository):
    model: EndUser = EndUser

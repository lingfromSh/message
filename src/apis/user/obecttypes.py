# First Library
import models
from common.graphql.relay import TortoiseORMNode


class UserTortoiseORMNode(TortoiseORMNode):
    class Meta:
        model = models.User

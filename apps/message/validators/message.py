from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import constr
from pydantic import model_validator

from apps.message.common.constants import MessageStatus

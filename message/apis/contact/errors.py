# Third Party Library
import strawberry


@strawberry.interface
class ResponseError:
    message: str


@strawberry.type
class ContactDuplicateCodeError(ResponseError):
    code: str

# JSONRPC Custom Errors
from pydantic import BaseModel

from app.utils.fastapi_ex import jsonrpc


class EmptyValue(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'Empty Value'

    class DataModel(BaseModel):
        details: str


class AuthenticationError(jsonrpc.BaseError):
    CODE = 5001
    MESSAGE = 'Authentication error'

    class DataModel(BaseModel):
        details: str


class UserNotFound(jsonrpc.BaseError):
    CODE = 5002
    MESSAGE = 'User not found.'

    class DataModel(BaseModel):
        details: str


class ErrorCreatingUser(jsonrpc.BaseError):
    CODE = 5003
    MESSAGE = 'Cannot create user in database.'

    class DataModel(BaseModel):
        details: str


class ErrorCreatingUserInPool(jsonrpc.BaseError):
    CODE = 5004
    MESSAGE = 'Cannot create user in the pool.'

    class DataModel(BaseModel):
        details: str


class ErrorDeletingUserFromPool(jsonrpc.BaseError):
    CODE = 5005
    MESSAGE = 'Cannot delete user from the pool.'

    class DataModel(BaseModel):
        details: str


class DuplicateEmail(jsonrpc.BaseError):
    CODE = 5006
    MESSAGE = 'Email already exists.'

    class DataModel(BaseModel):
        details: str


class DuplicateUsername(jsonrpc.BaseError):
    CODE = 5007
    MESSAGE = 'Username already exists.'

    class DataModel(BaseModel):
        details: str


class ValueOutOfRange(jsonrpc.BaseError):
    CODE = 5008
    MESSAGE = 'The value is out of range.'

    class DataModel(BaseModel):
        details: str


class UnknownError(jsonrpc.BaseError):
    CODE = 9000
    MESSAGE = 'Unknown error'

    class DataModel(BaseModel):
        details: str

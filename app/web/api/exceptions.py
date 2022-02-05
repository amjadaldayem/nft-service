# JSONRPC Custom Errors
import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel


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


class UnknownError(jsonrpc.BaseError):
    CODE = 9000
    MESSAGE = 'Unknown error'

    class DataModel(BaseModel):
        details: str

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

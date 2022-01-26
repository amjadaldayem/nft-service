# JSONRPC Custom Errors
import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel


class AuthenticationError(jsonrpc.BaseError):
    CODE = 5001
    MESSAGE = 'Authentication error'

    class DataModel(BaseModel):
        details: str
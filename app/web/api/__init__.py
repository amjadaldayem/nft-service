import os

import fastapi_jsonrpc as jsonrpc
from fastapi import Body, Depends
from mangum import Mangum
from pydantic import BaseModel

from app import settings  # noqa

from app.models.user import User
from app.web.api.dependencies import get_auth_user

app = jsonrpc.API()

api_v1_noauth = jsonrpc.Entrypoint('/v1/rpc')
api_v1_auth = jsonrpc.Entrypoint('/v1/_rpc')


class EmptyValue(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'Empty Value'

    class DataModel(BaseModel):
        details: str


@api_v1_noauth.method(errors=[EmptyValue])
def echo(
        data: str = Body(..., example='123'),
) -> str:
    if not data:
        raise ValueError("Empty data")
    else:
        return data + '\n' + os.environ['COGNITO_PUBLIC_KEYS']


@api_v1_auth.method(errors=[EmptyValue])
def echo(
        data: str = Body(..., example='123'),
        user: User = Depends(get_auth_user),
) -> str:
    if not data:
        raise ValueError("Empty data")
    else:
        return f"From authenticated user {user.user_id} : {data}"


app.bind_entrypoint(api_v1_noauth)
app.bind_entrypoint(api_v1_auth)

handler = Mangum(app=app)

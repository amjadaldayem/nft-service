import fastapi_jsonrpc as jsonrpc
from fastapi import Body, Depends, Header
from mangum import Mangum
from pydantic import BaseModel

from app.models.user import User

app = jsonrpc.API()

api_v1_noauth = jsonrpc.Entrypoint('/v1/rpc')
api_v1_auth = jsonrpc.Entrypoint('/v1/_rpc')


class MyError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'My error'

    class DataModel(BaseModel):
        details: str


@api_v1_noauth.method(errors=[MyError])
def echo(
        data: str = Body(..., example='123'),
) -> str:
    if data == 'error':
        raise MyError(data={'details': 'error'})
    else:
        return data


def get_auth_user(
        authroization: str = Header(None)
) -> User:
    pass


@api_v1_auth.method(errors=[MyError])
def echo(
        data: str = Body(..., example='123'),
        user: User = Depends(get_auth_user),
) -> str:
    if data == 'error':
        raise MyError(data={'details': 'error'})
    else:
        return data


app.bind_entrypoint(api_v1_noauth)
app.bind_entrypoint(api_v1_auth)

handler = Mangum(app=app)

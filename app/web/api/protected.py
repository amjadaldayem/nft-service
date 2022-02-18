import orjson
from fastapi import (
    Body,
    Depends
)

from app import settings  # noqa
from app.models.user import User
from app.web.api.dependencies import get_auth_user
from .entry import (
    app,
    api_v1_auth
)
from ..exceptions import (
    EmptyValue
)


@api_v1_auth.method(errors=[EmptyValue])
def echo(
        data: str = Body(..., example='123'),
        user: User = Depends(get_auth_user),
) -> str:
    if not data:
        raise ValueError("Empty data")
    else:
        return f"From authenticated user : {data} {orjson.dumps(user)}"


@api_v1_auth.method(errors=[EmptyValue])
def get_user_data(user: User = Depends(get_auth_user)) -> User:
    return user


app.bind_entrypoint(api_v1_auth)

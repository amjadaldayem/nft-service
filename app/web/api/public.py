import os
import re
from typing import Dict

import pydantic
from fastapi import (
    Body
)
from pydantic import BaseModel, validator

from app.models.user import MAX_USERNAME_LEN, User
from app.web.services import user_service
from .entry import (
    app,
    api_v1_noauth
)
from .exceptions import EmptyValue


@api_v1_noauth.method()
def get_revision() -> str:
    return os.getenv('GITHUB_SHA', 'NONE')


class LoginInput(BaseModel):
    username: str
    password: pydantic.SecretStr

    @validator('username', allow_reuse=True)
    def regex_validator(cls, v):
        if len(v) < 2 or len(v) > MAX_USERNAME_LEN or not re.match(r'[a-zA-Z0-9_]', v):
            raise ValueError(f'Username length should be between 2 and {MAX_USERNAME_LEN}.')
        return v


class SignUpInput(LoginInput):
    email: pydantic.EmailStr


@api_v1_noauth.method(errors=[EmptyValue])
def sign_up(
        data: SignUpInput = Body(
            ...,
            example={
                'username': 'john', 'email': 'doe@example.com', 'password': '*****'
            }
        ),
) -> User:
    if not data:
        raise EmptyValue
    else:
        user = user_service.sign_up(
            data.email,
            data.username,
            data.password.get_secret_value()
        )
        return user


@api_v1_noauth.method(errors=[EmptyValue])
def login(
        data: LoginInput = Body(..., example="""
         'data': {'username': 'doe', 'password': '*****'}
        """),
) -> Dict[str, str]:
    if not data:
        raise EmptyValue
    else:
        access_token, refresh_token = user_service.login(
            username=data.username, password=data.password.get_secret_value()
        )
        return {'access_token': access_token, 'refresh_token': refresh_token}


app.bind_entrypoint(api_v1_noauth)

import os
import re
from typing import Dict

import pydantic
from fastapi import (
    Body
)
from pydantic import validator

from app.models.user import MAX_USERNAME_LEN, User
from app.web.services import user_service
from .entry import (
    jsonrpc_app,
    api_v1_noauth
)
from ..exceptions import EmptyValue
from ...models.shared import DataClassBase


@api_v1_noauth.method()
def get_revision() -> str:
    return os.getenv('GITHUB_SHA', 'NONE')


class LoginInput(DataClassBase):
    email: pydantic.EmailStr
    password: pydantic.SecretStr

    @validator('email')
    def email_validator(cls, v):
        """
        Alawys use lower case for emails.
        Args:
            v:

        Returns:

        """
        return v.lower()


class SignUpInput(LoginInput):
    nickname: str

    @validator('nickname', allow_reuse=True)
    def regex_validator(cls, v):
        if len(v) < 2 or len(v) > MAX_USERNAME_LEN or not re.match(r'[a-zA-Z0-9_]', v):
            raise ValueError(f'Nickname length should be between 2 and {MAX_USERNAME_LEN}.')
        return v


@api_v1_noauth.method(errors=[EmptyValue], response_model_by_alias=True)
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
            data.nickname,
            data.password.get_secret_value()
        )
        return user


@api_v1_noauth.method(errors=[EmptyValue])
def login(
        data: LoginInput = Body(..., example={
            'username': 'doe@example.com', 'password': '*****'
        }),
) -> Dict[str, str]:
    if not data:
        raise EmptyValue
    else:
        access_token, refresh_token = user_service.login(
            email=data.email, password=data.password.get_secret_value()
        )
        return {'accessToken': access_token, 'refreshToken': refresh_token}


jsonrpc_app.bind_entrypoint(api_v1_noauth)

import os
import time
from typing import Dict, List

from fastapi import (
    Body
)

from app.models.user import User
from app.web.services import user_service
from .entry import (
    jsonrpc_app,
    api_v1_noauth
)
from .params import (
    LoginInput,
    SignUpInput,
    SecondaryMarketEventsInput,
)
from ..exceptions import EmptyValue
from ..services.nft import SmeNftResponseModel
from ... import settings


@api_v1_noauth.method()
def get_revision() -> str:
    return os.getenv('GITHUB_SHA', 'NONE')


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


@api_v1_noauth.method(errors=[EmptyValue])
def get_secondary_market_events() -> List[SmeNftResponseModel]:
    from app.web.services import nft_service

    starting_timestamp = int(time.time()) - settings.SME_FETCH_DEFAULT_LAG
    exclusive_start_key = (starting_timestamp, None, None)
    exclusive_stop_key = (starting_timestamp - 30, None, None)
    return nft_service.get_secondary_market_events(
        exclusive_start_key=exclusive_start_key,
        exclusive_stop_key=exclusive_stop_key,
        limit=15
    )


jsonrpc_app.bind_entrypoint(api_v1_noauth)

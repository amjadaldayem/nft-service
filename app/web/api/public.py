import os
import time
from typing import Dict, List, Optional

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
    NftInput
)
from ..exceptions import EmptyValue
from ..services.nft import (
    SmeNftResponseModel,
    NftResponseModel
)
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
def get_secondary_market_events(
        data: Optional[SecondaryMarketEventsInput] = Body(...),
) -> List[SmeNftResponseModel]:
    """
    For anonymous API call, the following params are fixed:
        - Timespan = 60 seconds Max
        - PageSize = 10 Max
    Args:
        data:

    Returns:

    """
    from app.web.services import nft_service
    data = data or SecondaryMarketEventsInput()
    # The latest timestamp we allow anonymous use to start fetching.
    latest_allowed_starting_timestamp = int(time.time()) - settings.SME_FETCH_DEFAULT_LAG
    exclusive_start_key = data.exclusive_start_key

    timespan = data.timespan
    if timespan > 60:
        timespan = 60

    if not exclusive_start_key or exclusive_start_key[0] > latest_allowed_starting_timestamp:
        exclusive_start_key = (latest_allowed_starting_timestamp, None, None)
    exclusive_stop_key = data.exclusive_stop_key

    if not exclusive_stop_key:
        exclusive_stop_key = (exclusive_start_key[0] - timespan, None, None)

    return nft_service.get_secondary_market_events(
        exclusive_start_key=exclusive_start_key,
        exclusive_stop_key=exclusive_stop_key,
        limit=settings.SME_FETCH_PAGE_SIZE
    )


@api_v1_noauth.method(errors=[EmptyValue])
def get_nft(
        data: NftInput = Body(...),
) -> NftResponseModel:
    """
    For anonymous API call, the following params are fixed:
        - Timespan = 60 seconds Max
        - PageSize = 10 Max
    Args:
        data:

    Returns:

    """
    from app.web.services import nft_service
    return nft_service.get_nft(
        nft_id=data.nft_id,
        nft_name_slug=data.nft_name_slug
    )


jsonrpc_app.bind_entrypoint(api_v1_noauth)

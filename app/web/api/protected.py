from typing import List

from fastapi import (
    Body,
    Depends
)

from app import settings  # noqa
from app.models.user import User
from app.web.api.dependencies import get_auth_user
from . import SecondaryMarketEventsInput
from .entry import (
    jsonrpc_app,
    api_v1_auth
)
from ..exceptions import (
    EmptyValue
)
from ..services.nft import SmeNftResponseModel


@api_v1_auth.method(errors=[EmptyValue])
def echo(
        data: str = Body(..., example='123'),
        user: User = Depends(get_auth_user),
) -> str:
    if not data:
        raise ValueError("Empty data")
    else:
        return f"From authenticated user : {data} {user.json()}"


@api_v1_auth.method(errors=[EmptyValue])
def get_user_data(user: User = Depends(get_auth_user)) -> User:
    return user


@api_v1_auth.method()
def get_secondary_market_events(
        data: SecondaryMarketEventsInput = Body(...),
        user: User = Depends(get_auth_user)
) -> List[SmeNftResponseModel]:
    from app.web.services import nft_service

    return nft_service.get_secondary_market_events(
        exclusive_start_key=data.exclusive_start_key,
        exclusive_stop_key=data.exclusive_stop_key,
        timespan=data.timespan,
        limit=50,
        user=user,
        blockchain_ids=data.blockchain_ids,
        event_types=data.event_types,
    )


jsonrpc_app.bind_entrypoint(api_v1_auth)

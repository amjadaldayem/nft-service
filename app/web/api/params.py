# Centralized place for API input models & validators.
import re
import time
from typing import Optional, Tuple, Set

import pydantic
from pydantic import validator

from app import settings
from app.blockchains import (
    BLOCKCHAIN_SOLANA,
    SECONDARY_MARKET_EVENT_LISTING,
    SECONDARY_MARKET_EVENT_DELISTING,
    SECONDARY_MARKET_EVENT_BID,
    SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
    SECONDARY_MARKET_EVENT_SALE,
    SECONDARY_MARKET_EVENT_SALE_AUCTION,
    SECONDARY_MARKET_EVENT_PRICE_UPDATE,
)
from app.models.shared import DataClassBase
from app.models.user import MAX_USERNAME_LEN
from app.web.exceptions import ValueOutOfRange


class SecondaryMarketEventsInput(DataClassBase):
    # The key from which to continue fetching. This value *should be*
    # a tuple of (tiemstamp, blockchain_id, transaction_hash) which is
    # all available on each item returned from previous API.
    #
    # Imagine this as an anchor for fetching the "next" page.
    # The format:
    #   (timestamp, blockchain - can be None, transaction_hash - can be None).
    # If not set, will choose the latest event from `settings.SME_FETCH_DEFAULT_LAG`
    # seconds ago from the current timestamp.
    # (
    #   curr_timestamp - settings.SME_FETCH_DEFAULT_LAG, None, None
    # )
    #
    exclusive_start_key: Optional[Tuple[int, Optional[int], Optional[str]]] = pydantic.Field(
        alias="exclusiveStartKey",
        default_factory=lambda: (
            int(time.time()) - settings.SME_FETCH_DEFAULT_LAG,
            None,
            None,
        )
    )

    # The timespan of events we fetch.
    # This param will be ignored when `exclusive_stop_key` is present, because
    # we will eventually try to "stop" at that `exclusive_stop_key`.
    timespan: int = 30

    page_size: int = 25

    # The key to which we stop fetching.
    exclusive_stop_key: Optional[Tuple[int, Optional[int], Optional[str]]] = pydantic.Field(
        None, alias="exclusiveStopKey"
    )

    # Filters below,
    # Might want to add to this list later once we support more blockchains
    blockchain_ids: Set[int] = pydantic.Field(
        default_factory=lambda: {BLOCKCHAIN_SOLANA, }
    )
    event_types: Set[int] = pydantic.Field(
        default_factory=lambda: {
            SECONDARY_MARKET_EVENT_LISTING,
            SECONDARY_MARKET_EVENT_DELISTING,
            SECONDARY_MARKET_EVENT_SALE,
            SECONDARY_MARKET_EVENT_PRICE_UPDATE,
            SECONDARY_MARKET_EVENT_BID,
            SECONDARY_MARKET_EVENT_SALE_AUCTION,
            SECONDARY_MARKET_EVENT_CANCEL_BIDDING,
        }
    )

    @validator('timespan', allow_reuse=True)
    def validate_timespan(cls, v):
        if v < 15 or v > 360:
            raise ValueOutOfRange(
                data={'details': f'Value {v} is out of range [15, 360].'}
            )
        return v

    @validator('page_size', allow_reuse=True)
    def validate_page_size(cls, v):
        if v > 50 or v < 1:
            raise ValueOutOfRange(
                data={'details': f'Value {v} is out of range [1, 50].'}
            )
        return v


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

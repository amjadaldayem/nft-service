# Centralized place for API input models & validators.
import re
from typing import Optional

import pydantic
from pydantic import validator

from app.models.shared import DataClassBase
from app.models.user import MAX_USERNAME_LEN
from app.web.exceptions import ValueOutOfRange


class SecondaryMarketEventsInput(DataClassBase):
    # The key from which to continue fetching. This value *should be*
    # the `last_evaluated_key` returned from previous call to
    # get_secondary_market_events API.
    #
    # Imagine this as an anchor for fetching the "next" page.
    #
    # If not set, will choose the latest event from 6 minutes ago
    # from the current timestamp.
    exclusive_start_key: Optional[str] = None

    # The `direction` we want to go from the anchor (exclusive_start_key)
    # By default, always go to more recent events.
    forward: bool = True

    # The timespan of events we fetch. Depending on the direction we go,
    # this can be either spanning backward or forward. By default, 3 minutes
    # worth of data.
    timespan: int = 180

    @validator('timespan')
    def validate_timespan(cls, v):
        if v < 15 or v > 360:
            raise ValueOutOfRange(
                data={'details': f'Value {v} is out of range [15, 360].'}
            )
        return v


class SecondaryMarketEventsOutput(DataClassBase):

    @classmethod
    def make_key(cls, pk, sk):
        """
        Makes a user facing key out of (pk, sk) of an event to obfuscate
        underlying data schema.

        Returns:

        """

    @classmethod
    def extract_key(cls, k):
        """
        Extracts the user facing key into (pk, sk).

        Args:
            k:

        Returns:

        """

    last_evaluated_key: Optional[str] = None


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

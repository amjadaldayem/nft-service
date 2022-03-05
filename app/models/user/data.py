import datetime

from app.models.shared import DataClassBase

# Constants

MIN_USERNAME_LEN = 2
MAX_USERNAME_LEN = 36
MAX_EMAIL_LEN = 64


class User(DataClassBase):
    user_id: str
    username: str
    preferred_username: str
    email: str
    phone_number: str = ''
    nickname: str = ''
    is_admin: bool = False
    joined_on: datetime.datetime = datetime.datetime(year=1970, month=1, day=1)

    @property
    def sme_lagging(self):
        """
        Value in second. The minimal allowed lagging for querying the SME.

        A user cannot query secondary market events that happend after the
        following timestamp,

            current_timestamp - user.sme_lagging

        TODO: This could be a per user value. E.g., depending on payment status.

        """
        return 180 if not self.is_admin else 60

    @property
    def bookmarked_nft_ids(self):
        """
        TODO: Implement the fetching here or in the model
        Returns:

        """
        return set()

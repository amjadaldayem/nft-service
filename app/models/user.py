import datetime

from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    username: str
    preferred_username: str
    email: str
    phone_number: str = ''
    joined_on: datetime.datetime = datetime.datetime(year=1970, month=1, day=1)


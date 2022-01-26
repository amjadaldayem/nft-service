import datetime

from pydantic import BaseModel

from app import settings


class User(BaseModel):
    user_id: str
    username: str
    preferred_username: str
    email: str
    phone_number: str = ''
    joined_on: datetime.datetime = datetime.datetime(year=1970, month=1, day=1)


class UserRepository:

    def __init__(self, dynamodb_resource):
        self.dynamodb_resource = dynamodb_resource
        # This table *must* exists ahead of time.
        self.table = dynamodb_resource.Table(settings.DYNAMODB_USER_TABLE)

    def get_user(self, user_id):
        pass

    def query_users(self, **kwargs):
        pass

    def create_user(self, user: User):

    def update_user(self, user_id: str, **kwargs):
        pass

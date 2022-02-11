import copy
import datetime
from typing import Optional

from pydantic import BaseModel

from app import settings

# Constants
from app.models.dynamo import DynamoDBRepositoryBase

MIN_USERNAME_LEN = 2
MAX_USERNAME_LEN = 36
MAX_EMAIL_LEN = 64


class User(BaseModel):
    user_id: str
    username: str
    preferred_username: str
    email: str
    phone_number: str = ''
    joined_on: datetime.datetime = datetime.datetime(year=1970, month=1, day=1)


class UserRepository(DynamoDBRepositoryBase):
    """
    user table

    pk           sk
    <user_id>    p
                 b#<blockchain_id>#n#<token_address> ...nft metadata...   <-- Bookmarked NFTs per blockchain

    """
    PK = 'pk'
    SK = 'sk'

    def __init__(self, dynamodb_resource):
        super().__init__(
            settings.DYNAMODB_USER_TABLE,
            dynamodb_resource,
        )

    def get_user_profile(self, user_id) -> Optional[User]:
        table = self.table
        resp = table.get_item(
            Key={
                self.PK: user_id,
                self.SK: 'p'
            },
        )
        item_dict = resp['Item']
        item_dict['user_id'] = item_dict['pk']
        item_dict['joined_on'] = datetime.datetime.fromisoformat(item_dict['joined_on'])
        del item_dict['sk']
        return User(**item_dict)

    def query_users(self, **kwargs):
        pass

    def save_user_profile(self, user: User, overwrite=False) -> None:
        """
        Creates a new user in DB.
        Args:
            user:
            overwrite: If set to true, user with the same ID will be overwritten
                otherwise will throw Duplicate exception

        Returns:

        """
        table = self.table
        item = copy.copy(user.__dict__)
        del item['user_id']
        item[self.PK] = user.user_id
        item[self.SK] = 'p'
        item['joined_on'] = user.joined_on.isoformat()
        resp = table.put_item(
            Item=item,
            ReturnValues=self.RV_NONE
        )

    def update_user(self, user_id: str, **kwargs):
        pass

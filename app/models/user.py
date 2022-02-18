import copy
import datetime
from typing import Optional

from pydantic import dataclasses

# Constants
from app.models import meta
from app.models.dynamo import DynamoDBRepositoryBase
from .shared import DataclassBase

MIN_USERNAME_LEN = 2
MAX_USERNAME_LEN = 36
MAX_EMAIL_LEN = 64


@dataclasses.dataclass
class User(DataclassBase):
    user_id: str
    username: str
    preferred_username: str
    email: str
    phone_number: str = ''
    joined_on: datetime.datetime = datetime.datetime(year=1970, month=1, day=1)


class UserRepository(DynamoDBRepositoryBase, meta.DTUserMeta):
    """
    user table

    pk           sk
    <user_id>    p
                 bn#<nft_id> ...nft metadata...   <-- Bookmarked NFTs per blockchain

    """

    def __init__(self, dynamodb_resource):
        super().__init__(
            self.NAME,
            dynamodb_resource,
        )

    def get_user(self, user_id) -> Optional[User]:
        table = self.table
        resp = table.get_item(
            Key={
                self.PK: user_id,
                self.SK: 'p'
            },
        )
        item_dict = resp['Item']
        return self.user_from_dynamo(item_dict)

    @classmethod
    def user_to_dynamo(cls, user: User):
        item = copy.copy(user.__dict__)
        del item['user_id']
        item[cls.PK] = user.user_id
        item[cls.SK] = 'p'
        item['joined_on'] = user.joined_on.isoformat()
        return item

    @classmethod
    def user_from_dynamo(cls, item_dict):
        item_dict['user_id'] = item_dict[cls.PK]
        del item_dict[cls.PK]
        item_dict['joined_on'] = datetime.datetime.fromisoformat(item_dict['joined_on'])
        if cls.SK in item_dict:
            del item_dict['sk']
        if '__initialised__' in item_dict:
            del item_dict['__initialised__']
        return User(**item_dict)

    def query_users(self, **kwargs):
        pass

    def save_user_profile(self, user: User, overwrite=False):
        """
        Creates a new user in DB.
        Args:
            user:
            overwrite: If set to true, user with the same ID will be overwritten
                otherwise will throw Duplicate exception

        Returns:

        """
        table = self.table
        try:
            table.put_item(
                Item=self.user_to_dynamo(user),
                ReturnValues=self.RV_NONE
            )
        except:
            raise

    def update_user(self, user_id: str, **kwargs):
        pass

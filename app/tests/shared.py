import functools
import os.path
from typing import Union, Tuple, List

import orjson

from app import settings
from app.models import SecondaryMarketEvent, NftData
from app.models.shared.dynamo import SchemaParser


def create_tables(client):
    schema_file = os.path.join(
        settings.PROJECT_BASE_PATH,
        'app',
        'models',
        'schemas.yml'
    )
    table_schema_dict = SchemaParser.load_schema_file(schema_file)
    for _, v in table_schema_dict.items():
        v.create_from_api(client)


def cognito_create_user_pool_and_client(cognito_client) -> Union[str, str]:
    """
    Creates a Cognito User Pool for test

    Args:
        cognito_client:

    Returns:

    """
    user_pool_creation_args = {
        'Policies': {
            'PasswordPolicy': {
                'MinimumLength': 6,
                'RequireNumbers': True
            }
        },
        'PoolName': 'test-user-pool',
        'AdminCreateUserConfig': {
            'AllowAdminCreateUserOnly': True
        },
        'AutoVerifiedAttributes': [
            'email',
        ],
        'AliasAttributes': [
            'phone_number',
            'email',
            'preferred_username'
        ],
        'Schema': [
            {
                'Name': 'email',
                'Required': True,
                'Mutable': True,
                'AttributeDataType': 'String'
            },
            {
                'Name': 'preferred_username',
                'Required': True,
                'Mutable': True,
                'AttributeDataType': 'String'
            },
            {
                'Name': 'phone_number',
                'Required': False,
                'Mutable': True,
                'AttributeDataType': 'String'
            },
            {
                'Name': 'joined_on',
                'Required': False,
                'Mutable': False,
                'AttributeDataType': 'DateTime'
            }
        ],
    }
    user_pool = cognito_client.create_user_pool(
        **user_pool_creation_args
    )['UserPool']
    user_pool_id = user_pool['Id']
    user_pool_client = cognito_client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='test-user-pool-client',
    )['UserPoolClient']
    return user_pool_id, user_pool_client['ClientId']


@functools.lru_cache
def get_data_path(*args):
    return os.path.join(
        os.path.dirname(__file__),
        "data",
        *args
    )


def load_sme_and_nft_data_list_from_file(blockchain, filename) -> List[Tuple[SecondaryMarketEvent, NftData]]:
    """
    Loads a list of (sme, nft_data) pair from a json file.
    Args:
        blockchain:
        filename:

    Returns:

    """
    p = get_data_path(blockchain, filename)
    ret = []
    with open(p, 'r') as fd:
        data = orjson.loads(fd.read())
        for (p1, p2) in data:
            ret.append(
                (
                    SecondaryMarketEvent(**p1),
                    NftData(**p2)
                )
            )
        return ret

import contextlib
from functools import cached_property

import boto3

from app import settings
from app.models.sme import SecondaryMarketEvent


class NFTRepository:
    """
    pk            sk




    """

    def __init__(self,
                 table_name,
                 region='us-west-2',
                 endpoint_url=None
                 ):
        self.table_name = table_name
        self.session = boto3.Session()
        self.kwargs = {
            'region_name': region
        }
        if endpoint_url:
            self.kwargs['endpoint_url'] = endpoint_url
        self.resource = self.session.resource('dynamodb', **self.kwargs)

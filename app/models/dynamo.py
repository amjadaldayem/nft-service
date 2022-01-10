import contextlib

import boto3

from app import settings


class NFTRepository:
    """
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

    @contextlib.asynccontextmanager
    def table(self):
        with self.session.resource('dynamodb', **self.kwargs) as dynamo_resource:
            yield dynamo_resource.Table(self.table_name)

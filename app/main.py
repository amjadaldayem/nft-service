import sys

import asyncclick as click
import boto3

import settings
from app.models.dynamo import NFTRepository
from slab.logging import setup_logging
from slab.errors import setup_error_handler
from app.tools import (
    solana,
)

sys.dont_write_bytecode = True


def sentry_error_notify(e, metadata):
    pass


def stderr_error_notify(e, metadata):
    pass


def initialize():
    # Initialize
    dynamodb_endpoint = settings.DYNAMODB_ENDPOINT
    region_name = settings.AWS_REGION
    env = settings.DEPLOYMENT_ENV
    table_name = f"{env}_nft"
    dynamodb_resource = boto3.resource(
        'dynamodb',
        endpoint_url=dynamodb_endpoint,
        region_name=region_name
    )
    # NFTRepository.initialize(table_name)


@click.group()
async def main():
    setup_logging(settings.DEBUG)
    setup_error_handler(
        stderr_error_notify
        if settings.DEPLOYMENT_ENV == 'local'
        else sentry_error_notify
    )
    initialize()


main.add_command(solana)

if __name__ == '__main__':
    main(_anyio_backend='asyncio')

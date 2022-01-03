import logging
import sys

import asyncclick as click
import orjson

import settings
from app.tools import tk
from app.worker import worker
from slab.errors import setup_error_handler, full_stacktrace
from slab.logging import setup_logging

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


async def sentry_error_notify(e, metadata):
    pass


def initialize():
    # # Initialize
    # dynamodb_endpoint = settings.DYNAMODB_ENDPOINT
    # region_name = settings.AWS_REGION
    # env = settings.DEPLOYMENT_ENV
    # table_name = f"{env}_nft"
    # dynamodb_resource = boto3.resource(
    #     'dynamodb',
    #     endpoint_url=dynamodb_endpoint,
    #     region_name=region_name
    # )
    # # NFTRepository.initialize(table_name)
    pass


@click.group()
async def main():
    setup_logging(settings.DEBUG)
    if settings.DEPLOYMENT_ENV not in ('local', 'test'):
        setup_error_handler(sentry_error_notify)
    initialize()


main.add_command(tk)
main.add_command(worker)

if __name__ == '__main__':
    main(_anyio_backend='asyncio')

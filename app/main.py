import logging
import os
import sys

import click

import settings
from app.tools import tk
from app.worker import worker
from app.worker.indexers.solana.nft_indexer import NftCollectionDRoutine as SolanaNftCollectionDRoutine
from slab.errors import setup_error_handler
from slab.logging import setup_logging
from slab.messaging import map_droutines_to_queue, CQueue

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


def sentry_error_notify(e, metadata):
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
    map_droutines_to_queue(
        SolanaNftCollectionDRoutine
    )


@click.group()
def main():
    setup_logging(settings.DEBUG)
    if settings.DEPLOYMENT_ENV not in ('local', 'test'):
        setup_error_handler(sentry_error_notify)
    initialize()


main.add_command(tk)
main.add_command(worker)

if __name__ == '__main__':
    main()

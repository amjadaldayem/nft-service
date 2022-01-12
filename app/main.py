import logging
import sys

import click

import settings
from app.tools import tk
from app.worker import worker
from app.worker.indexers.solana.nft_indexer import (
    NftCollectionDRoutine as SolanaNftCollectionDRoutine
)
from app.worker.indexers.terra.nft_indexer import (
    NftCollectionDRoutine as TerraNftCollectionDRoutine
)
from slab.errors import setup_error_handler
from slab.logging import setup_logging

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


def sentry_error_notify(e, metadata):
    pass


def initialize():
    settings.map_droutines_to_queue(
        settings.NFT_COLLECTION_CRAWL_QUEUE_URL,
        SolanaNftCollectionDRoutine,
        TerraNftCollectionDRoutine
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

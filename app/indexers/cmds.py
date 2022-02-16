from typing import Set

import click

from .solana import (
    do_solana_sme
)


@click.command(name='solana-sme')
@click.argument('stream-name', nargs=1)
@click.argument('market-ids', nargs=-1)
@click.option('-t', '--runtime', type=int, default=0)
@click.option('--region', type=str, default='us-west-2')
@click.option('--endpoint-url', type=str, default=None)
def solana_sme(stream_name, market_ids: Set[int], runtime, region, endpoint_url):
    """
    Starts Solana Secondary Market Events listener on Market Id set or `all`.
    """
    return do_solana_sme(stream_name, market_ids, runtime, region, endpoint_url)


@click.group()
def indexer():
    """
    Start indexers.
    """
    pass


indexer.add_command(solana_sme)

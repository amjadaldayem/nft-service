import asyncclick as click
from .sme_indexer import sme_index_secondary_market


@click.group()
async def solana():
    """
    Indexers command.

    """
    return

solana.add_command(sme_index_secondary_market)
import asyncclick as click
from .solana import solana


@click.group()
async def indexers():
    """
    Indexers command.

    """
    return


indexers.add_command(solana)

import asyncclick as click
from .transaction import txn  # noqa


@click.group()
async def solana():
    """
    Tools for Solana blockchain.

    """
    return


solana.add_command(txn)

import asyncclick as click
from .solana import solana  # noqa


@click.group()
async def tk():
    """
    Toolkit - Useful tools for exploring blockchains

    """
    return

tk.add_command(solana)

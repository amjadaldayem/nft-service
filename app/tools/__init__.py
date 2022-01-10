import click
from .solana import solana  # noqa


@click.group()
def tk():
    """
    Toolkit - Useful tools for exploring blockchains

    """
    return

tk.add_command(solana)

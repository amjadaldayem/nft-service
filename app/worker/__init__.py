import click
from .entry import start


@click.group()
def worker():
    """
    Indexers command.

    """
    return


worker.add_command(start)

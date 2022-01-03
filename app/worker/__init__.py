import asyncclick as click
from .entry import start


@click.group()
async def worker():
    """
    Indexers command.

    """
    return


worker.add_command(start)

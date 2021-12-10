import sys

import asyncclick as click

import settings
from app.slab.logging import setup_logging
from app.tools import (
    txn,
)

sys.dont_write_bytecode = True


@click.group()
async def main():
    setup_logging(settings.DEBUG)

main.add_command(txn)


if __name__ == '__main__':
    main(_anyio_backend='asyncio')

import sys

import asyncclick as click

import settings
from app.slab.logging import setup_logging

sys.dont_write_bytecode = True


@click.group()
async def main():
    setup_logging(settings.DEBUG)


if __name__ == '__main__':
    main(_anyio_backend='asyncio')

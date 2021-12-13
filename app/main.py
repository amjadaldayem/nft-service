import sys

import asyncclick as click

import settings
from app.slab.logging import setup_logging
from app.slab.errors import setup_error_handler
from app.tools import (
    txn,
)

sys.dont_write_bytecode = True


def sentry_error_notify(e, metadata):
    pass


def stderr_error_notify(e, metadata):
    pass


@click.group()
async def main():
    setup_logging(settings.DEBUG)
    setup_error_handler(
        stderr_error_notify
        if settings.DEPLOYMENT_ENV == 'local'
        else sentry_error_notify
    )


main.add_command(txn)

if __name__ == '__main__':
    main(_anyio_backend='asyncio')

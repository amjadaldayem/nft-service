# Entrypoint for commandline toolkit
import logging
import sys

import click

import settings
from app.tools import solana
from app.utils import setup_error_handler
from app.utils import setup_logging

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


def sentry_error_notify(e, metadata):
    pass


def initialize():
    setup_logging(settings.DEBUG)
    if settings.DEPLOYMENT_ENV not in ('local', 'test'):
        setup_error_handler(sentry_error_notify)


@click.group()
def main():
    initialize()


main.add_command(solana)

if __name__ == '__main__':
    # Entry point for tools and other stuff.
    main()

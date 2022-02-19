# Entrypoint for commandline toolkit
import logging
import sys

import click

from app import settings  # noqa
from app.indexers.cmds import indexer
from app.toolkit.cmds import toolkit

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


main.add_command(toolkit)
main.add_command(indexer)

if __name__ == '__main__':
    # Entry point for tools and other stuff.
    main()

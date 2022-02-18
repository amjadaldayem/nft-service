# Entrypoint for commandline toolkit
import logging
import sys

import click
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import (
    AwsLambdaIntegration,
)

from app.indexers.cmds import indexer
from app.toolkit.cmds import toolkit
from app.utils import setup_error_handler
from app.utils import setup_logging

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


def sentry_error_notify(e, metadata):
    sentry_sdk.capture_exception(e, extra=metadata)


def initialize(is_lambda=False):
    from app import settings
    setup_logging(settings.DEBUG)
    integrations = []
    if is_lambda:
        integrations.append(AwsLambdaIntegration())

    sentry_sdk.init(
        dsn=settings.SENTRY_IO_DSN,
        integrations=integrations,
        traces_sample_rate=settings.SENTRY_IO_TRACE_SAMPLERATE,
        debug=settings.SENTRY_IO_DEBUG,
        with_locals=settings.SENTRY_IO_WITH_LOCALS,
        max_breadcrumbs=settings.SENTRY_IO_MAX_BREADCRUMBS,
        request_bodies=settings.SENTRY_IO_CAPTURE_REQUEST_BODIES,
        environment=settings.DEPLOYMENT_ENV
    )
    if settings.DEPLOYMENT_ENV not in ('local', 'test'):
        setup_error_handler(sentry_error_notify)


@click.group()
def main():
    initialize()


main.add_command(toolkit)
main.add_command(indexer)

if __name__ == '__main__':
    # Entry point for tools and other stuff.
    main()

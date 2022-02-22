import logging
import os

from .logtail import LogtailHandler

NOISY_MODULES = (
    "botocore",
    "botocore.hooks",
    "botocore.auth",
    "botocore.credentials",
    "boto3",
    "ddtrace",
    "requests",
    "s3transfer",
    "urllib3",
    "mangum.lifespan",
    "mangum.http",
    "sentry_sdk.errors",
    "asyncio",
    "websockets.client"
)


def setup_logging(debug=0, include_noisy=None, disable_existing=True,
                  **kwargs):
    """
    Sets up logging for an app.

    Args:
        debug (int): An integer determining what producer_mode of debugging output to
                     display. 0 disables debug, 1 enables it but disables
                     debug logging from noisy libraries like boto, 2 enables
                     debugging fully.
        include_noisy (list): A list of "noisy modules" to exclude with debug.
        disable_existing (bool): If true, first disable all existing logging
                                 handlers before setting up logging. Allows us
                                 to throw out things that cause duplicate
                                 logging.
    """
    if disable_existing:
        del (logging.root.handlers[:])
    include_noisy = include_noisy or []
    log_level = logging.INFO

    debug = int(debug)

    if debug > 0:
        log_level = logging.DEBUG
    if debug < 2:
        for module in NOISY_MODULES:
            if module not in include_noisy:
                logging.getLogger(module).setLevel(logging.CRITICAL)

    log_format = (
        '[%(levelname)s] [%(asctime)s] [%(processName)s - '
        '%(process)d] %(name)s - %(message)s'
    )

    formatter = logging.Formatter(log_format)

    # if Logtail Token null, falls back to console logging.
    logtail_token = os.getenv('LOGTAIL_TOKEN')
    if not logtail_token or os.getenv('DEPLOYMENT_ENV') in ('test', 'local'):
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
    else:
        handler = LogtailHandler(
            source_token=logtail_token
        )

    logging.root.addHandler(handler)
    logging.root.setLevel(log_level)

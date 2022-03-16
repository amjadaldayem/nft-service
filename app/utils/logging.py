import logging
import os
import socket
from logging.handlers import SysLogHandler

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
    "websockets.client",
    "httpcore",
    "httpx",
    "solanaweb3",
)


def setup_logging(debug=0, include_noisy=None, disable_existing=True,
                  envs_with_console_logging=frozenset(),
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
        envs_with_console_logging: Environments for which we just use simple
            console logging instead of hooking up 3rd party log mgmt.
            E.g., for local and dev
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
        '[%(app_tag)s] [%(levelname)s] [%(asctime)s] [%(processName)s - '
        '%(process)d] %(name)s - %(message)s'
    )

    formatter = logging.Formatter(log_format)

    # if Logtail Token null, falls back to console logging.
    papertrail_address = os.getenv('PAPERTRAIL_ADDRESS')
    if not papertrail_address or os.getenv('DEPLOYMENT_ENV') in envs_with_console_logging:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
    else:
        class ContextFilter(logging.Filter):
            hostname = socket.gethostname()
            app_tag = os.getenv('APP_TAG', "unnamed")

            def filter(self, record):
                record.hostname = self.hostname
                record.app_tag = self.app_tag
                return True

        host, port = papertrail_address.split(":")
        handler = SysLogHandler(address=(host, int(port)))
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())

    logging.root.addHandler(handler)
    logging.root.setLevel(log_level)

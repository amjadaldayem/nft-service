import logging
import os
import socket

from .logdna import LogDNAHandler
from .system import get_secure_env

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


def setup_local_handler():
    class ContextFilter(logging.Filter):
        hostname = socket.gethostname()
        app = get_secure_env('APP_NAME', "unnamed")

        def filter(self, record):
            record.hostname = self.hostname
            record.app = self.app
            return True

    log_format = (
        '[%(app)s] [%(levelname)s] [%(asctime)s] [%(processName)s - '
        '%(process)d] %(name)s - %(message)s'
    )
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    return handler


def setup_3rd_party_handler(env):
    """
    Sets up 3rd party logging mgmt service.

    Returns:

    """
    ingestion_key = get_secure_env("LOGDNA_INGESTION_KEY")
    if not ingestion_key:
        # Falls back
        return setup_local_handler()

    options = {
        'hostname': socket.gethostname(),
        'index_meta': True,
        'app': get_secure_env("APP_NAME"),
        'env': env,
    }

    handler = LogDNAHandler(ingestion_key, options)

    return handler


def setup_logging(debug=0, include_noisy=None, disable_existing=True,
                  envs_with_console_logging=frozenset(), env=None,
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
        env: Current environment tag
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

    if os.getenv('DEPLOYMENT_ENV') in envs_with_console_logging:
        # Local Console logging
        handler = setup_local_handler()
    else:
        # Remote logging mgmt
        handler = setup_3rd_party_handler(env)

    logging.root.addHandler(handler)
    logging.root.setLevel(log_level)

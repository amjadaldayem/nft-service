import logging
import os
import socket
from logging.handlers import SysLogHandler

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

    class ContextFilter(logging.Filter):
        hostname = socket.gethostname()
        app_name = os.getenv('APP_NAME', "unnamed")

        def filter(self, record):
            record.hostname = self.hostname
            record.app_name = self.app_name
            return True
    log_format = (
        '[%(app_name)s] [%(levelname)s] [%(asctime)s] [%(processName)s - '
        '%(process)d] %(name)s - %(message)s'
    )
    formatter = logging.Formatter(log_format)

    syslog_address = os.getenv('SYSLOG_ADDRESS')
    if not syslog_address or os.getenv('DEPLOYMENT_ENV') in envs_with_console_logging:
        # Local Console logging
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())
    else:
        # Remote Syslog
        host, port = syslog_address.split(":")
        handler = SysLogHandler(address=(host, int(port)))
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())

    logging.root.addHandler(handler)
    logging.root.setLevel(log_level)

import logging
import socket
import sys

from sintra.config import settings

logging.basicConfig(
    format="[%(hostname)s] - [%(app)s] - [%(asctime)s] - [%(levelname)s] - [%(name)s] - [%(message)s]",
    level=logging.INFO,
    stream=sys.stdout,
)

old_factory = logging.getLogRecordFactory()
hostname = socket.gethostname()


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.hostname = hostname
    record.app = settings.worker.name

    return record


logging.setLogRecordFactory(record_factory)

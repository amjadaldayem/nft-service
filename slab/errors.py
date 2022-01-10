import asyncio.coroutines
import logging
import traceback
import sys
from typing import (
    Union, Awaitable,
)

import orjson

logger = logging.getLogger(__name__)


def stderr_error_notify(e, metadata):
    logger.error(
        "error=%s, metadata=%s, stacktrace=\n%s",
        str(e),
        orjson.dumps(metadata).decode(),
        full_stacktrace()
    )


_fn = stderr_error_notify


def setup_error_handler(fn):
    global _fn
    _fn = fn


def notify_error(e: Union[str, Exception], metadata=None):
    metadata = metadata or {}
    if _fn:
        try:
            _fn(e, metadata)
        except Exception as e:
            raise
    else:
        logger.error(str(e))


def full_stacktrace():
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]  # remove call of full_stack, the printed exception
        # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
        stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr

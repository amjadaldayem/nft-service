import logging
from typing import (
    Union,
)

logger = logging.getLogger(__name__)

_fn: callable = None


def setup_error_handler(fn):
    global _fn
    _fn = fn


def notify(e: Union[str, Exception], metadata=None):
    metadata = metadata or {}
    if _fn:
        try:
            _fn(e, metadata)
        except Exception as e:
            logger.error(str(e))
    else:
        logger.error(str(e))
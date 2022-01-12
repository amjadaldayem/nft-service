import logging

import click

from app import settings
from slab import messaging
from slab.messaging import CQueue

logger = logging.getLogger(__name__)


@click.command(name='start')
@click.option('-q', '--queue-urls', multiple=True, default=tuple())
@click.option('-m', '--max-messages-to-receive', required=False, default=None)
@click.option('-t', '--worker-type', required=False, default="generic")
def start(queue_urls, max_messages_to_receive, worker_type):
    logger.info(
        "Worker [%s] started. Max messages to receive: %s.",
        worker_type,
        max_messages_to_receive or '+∞',
    )
    if not queue_urls:
        logger.error("No queue URLs specified.")
        return

    messaging.droutine_worker_start(
        [
            CQueue(
                name=u,
                url=u,
                endpoint=settings.SQS_ENDPOINT
            ) for u in queue_urls
        ],
        max_messages_to_receive,
        worker_type
    )

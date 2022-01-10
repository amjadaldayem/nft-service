import logging

import click

from slab import messaging

logger = logging.getLogger(__name__)


@click.command(name='start')
@click.option('-q', '--queue-urls', multiple=True, default=tuple())
@click.option('-m', '--max-messages-to-receive', required=False, default=None)
@click.option('-t', '--worker-type', required=False, default="generic")
@click.option('-e', '--endpoint-url', required=False, default=None)
def start(queue_urls, max_messages_to_receive, worker_type, endpoint_url):
    logger.info(
        "Worker [%s] started. Max messages to receive: %s.",
        worker_type,
        max_messages_to_receive or '+∞',
    )
    if not queue_urls:
        logger.error("No queue URLs specified.")
        return

    # queues = [messaging.CQueue(u, name=u) for u in queue_urls]
    messaging.droutine_worker_start(queues, max_messages_to_receive, worker_type)

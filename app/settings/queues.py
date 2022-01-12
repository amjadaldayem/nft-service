import os

from url_normalize import url_normalize as _c

from slab.messaging import CQueue
from slab.messaging import map_droutines_to_queue as _map_droutines_to_queue

# TODO: List the Queue URLs here


NFT_COLLECTION_CRAWL_QUEUE_URL = _c(os.environ['NFT_COLLECTION_CRAWL_QUEUE_URL'])

ALL_QUEUE_URLS = (
    NFT_COLLECTION_CRAWL_QUEUE_URL,
)

SQS_ENDPOINT = os.getenv('SQS_ENDPOINT')

ALL_QUEUE_MAP = {
    nq: CQueue(name=nq, url=nq, endpoint=SQS_ENDPOINT)
    for nq in ALL_QUEUE_URLS
}


def map_droutines_to_queue(queue_url, *droutines):
    _map_droutines_to_queue(ALL_QUEUE_MAP[queue_url], *droutines)
